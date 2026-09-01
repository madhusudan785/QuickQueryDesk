"""Ticket API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.core.rate_limiter import ticket_rate_limiter
from app.database.session import get_db, async_session_factory
from app.models.user import User
from app.models.ticket import Ticket
from app.models.audit_log import AuditLog
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketReply,
    TicketResponse,
    TicketListResponse,
)
from app.schemas.audit_log import AuditLogResponse
from app.services.llm import classify_ticket, generate_draft_reply
from app.rag.engine import retrieve_relevant_articles
from app.rag.semantic_cache import semantic_cache
from app.websocket.manager import manager

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def _ticket_to_response(ticket: Ticket, employee_name: str | None = None) -> TicketResponse:
    """Convert a Ticket ORM instance to a TicketResponse schema."""
    return TicketResponse(
        id=ticket.id,
        employee_id=ticket.employee_id,
        employee_name=employee_name,
        title=ticket.title,
        description=ticket.description,
        attachment_filename=ticket.attachment_filename,
        ai_category=ticket.ai_category,
        current_category=ticket.current_category,
        ai_priority=ticket.ai_priority,
        current_priority=ticket.current_priority,
        status=ticket.status,
        ai_draft_reply=ticket.ai_draft_reply,
        final_reply=ticket.final_reply,
        rag_sources=ticket.rag_sources,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        resolved_by=ticket.resolved_by,
    )


def _ticket_to_list_response(ticket: Ticket, employee_name: str | None = None) -> TicketListResponse:
    """Convert a Ticket ORM instance to a TicketListResponse schema."""
    return TicketListResponse(
        id=ticket.id,
        title=ticket.title,
        current_category=ticket.current_category,
        current_priority=ticket.current_priority,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        employee_name=employee_name,
    )


async def _generate_draft_background(
    ticket_id: str,
    employee_id: str,
    title: str,
    description: str,
    category: str | None,
    priority: str | None,
):
    """Background task: RAG retrieval + AI draft generation (runs after classification).

    Classification has already been performed in create_ticket.
    This task handles RAG context retrieval and draft reply generation.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        query = f"{title} {description}"
        effective_cat = category or "Other"
        effective_pri = priority or "Medium"

        logger.info(f"AI Pipeline state for ticket {ticket_id}: GENERATING_DRAFT")

        # 1. RAG Retrieval (milliseconds on pre-warmed FAISS index)
        sources = await retrieve_relevant_articles(query, top_k=3)
        sources_json = [dict(s) for s in sources] if sources else None

        # 2. Draft Reply Generation (with automatic fallback on LLM failure)
        from app.services.llm import generate_draft_reply_ext
        draft, draft_status = await generate_draft_reply_ext(title, description, effective_cat, effective_pri)

        # 3. Store in Semantic Cache for future duplicate queries if classification & draft succeeded via LLM
        if category and priority and draft and draft_status == "COMPLETED":
            cache_payload = {
                "category": category,
                "priority": priority,
                "draft_reply": draft,
                "rag_sources": sources_json,
            }
            semantic_cache.set(query, cache_payload)

        # 4. Update DB row with draft + sources
        async with async_session_factory() as db:
            result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
            ticket = result.scalar_one_or_none()
            if ticket:
                ticket.ai_draft_reply = draft if draft else None
                ticket.rag_sources = sources_json
                await db.commit()

        logger.info(f"AI Pipeline state for ticket {ticket_id}: {draft_status}")
        await manager.notify_agents(
            "ticket_ai_ready",
            {
                "ticket_id": ticket_id,
                "state": draft_status,
                "category": category,
                "priority": priority,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Background draft generation failed for ticket {ticket_id}: {e}")
        # Generate safe fallback draft in case of critical background exception
        from app.services.llm import _create_fallback_draft
        fallback_draft = _create_fallback_draft(title, description, "")
        async with async_session_factory() as db:
            result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
            ticket = result.scalar_one_or_none()
            if ticket and not ticket.ai_draft_reply:
                ticket.ai_draft_reply = fallback_draft
                await db.commit()
        await manager.notify_agents(
            "ticket_ai_ready",
            {
                "ticket_id": ticket_id,
                "state": "COMPLETED_FALLBACK",
                "category": category,
                "priority": priority,
            },
        )



@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new support ticket. Employee only.

    Flow:
      1. Rate limiting check (2 tickets / 12h).
      2. Semantic cache check — if HIT, use cached classification + draft.
      3. If MISS, call LLM (Groq/Gemini) to classify (category + priority) with single-attempt execution.
         If classification fails, fallback routing defaults are used without claiming false AI suggestions.
      4. Launch background task for RAG retrieval + draft generation.
      5. WebSocket notifications dispatched with explicit state.
    """
    import logging
    logger = logging.getLogger(__name__)

    if current_user.role != "employee":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can create tickets")

    # 1. Rate Limiting Check (2 tickets / 12 hours)
    ticket_rate_limiter.check_rate_limit(current_user.id)

    query = f"{payload.title} {payload.description}"

    ticket = Ticket(
        employee_id=current_user.id,
        title=payload.title,
        description=payload.description,
        attachment_filename=payload.attachment_filename,
    )

    # 2. Semantic Cache Check (Vector Similarity >= 0.88)
    cached = semantic_cache.get(query)
    if cached:
        # Cache HIT — full result available instantly (0 LLM tokens, < 15ms)
        ticket.ai_category = cached["category"]
        ticket.current_category = cached["category"]
        ticket.ai_priority = cached["priority"]
        ticket.current_priority = cached["priority"]
        ticket.ai_draft_reply = cached["draft_reply"]
        ticket.rag_sources = cached["rag_sources"]
        logger.info("AI Pipeline state: COMPLETED (via Semantic Cache hit)")
    else:
        # Cache MISS — run LLM classification
        logger.info("AI Pipeline state: CLASSIFYING")
        classification = await classify_ticket(payload.title, payload.description)
        class_status = classification.get("status", "CLASSIFIED")

        if class_status == "CLASSIFIED" and not classification.get("is_fallback"):
            cat = classification["category"]
            pri = classification["priority"]
            ticket.ai_category = cat
            ticket.current_category = cat
            ticket.ai_priority = pri
            ticket.current_priority = pri
            logger.info(f"AI Pipeline state: CLASSIFIED (Category: {cat}, Priority: {pri})")
        else:
            ticket.ai_category = None
            ticket.current_category = "Other"
            ticket.ai_priority = None
            ticket.current_priority = "Medium"
            logger.warning("AI Pipeline state: CLASSIFICATION_FAILED (using fallback routing defaults)")

    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

    # 3. If Cache MISS, launch background task for RAG + draft generation
    if not cached:
        background_tasks.add_task(
            _generate_draft_background,
            str(ticket.id),
            current_user.id,
            payload.title,
            payload.description,
            ticket.ai_category,
            ticket.ai_priority,
        )

    # 4. Notify connected agents of new ticket creation via WebSocket
    await manager.notify_agents(
        "ticket_created",
        _ticket_to_list_response(ticket, employee_name=current_user.name).model_dump(mode="json"),
    )

    # 5. Notify the employee that classification is complete
    await manager.notify_employee(
        user_id=current_user.id,
        event="ticket_classified",
        data=_ticket_to_response(ticket, employee_name=current_user.name).model_dump(mode="json"),
    )

    return _ticket_to_response(ticket, employee_name=current_user.name)


@router.get("/my", response_model=list[TicketListResponse])
async def get_my_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get tickets for the current employee. Employee only."""
    if current_user.role != "employee":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can access this endpoint")

    result = await db.execute(
        select(Ticket)
        .where(Ticket.employee_id == current_user.id)
        .order_by(Ticket.created_at.desc())
    )
    tickets = result.scalars().all()
    return [_ticket_to_list_response(t, employee_name=current_user.name) for t in tickets]


@router.get("", response_model=list[TicketListResponse])
async def get_all_tickets(
    current_user: Annotated[User, Depends(require_role("agent"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = Query(None),
    priority: str | None = Query(None),
    search: str | None = Query(None),
):
    """Get all tickets with optional filters. Agent only."""
    query = select(Ticket, User.name).join(User, Ticket.employee_id == User.id)

    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if category:
        query = query.where(Ticket.current_category == category)
    if priority:
        query = query.where(Ticket.current_priority == priority)
    if search:
        query = query.where(Ticket.title.ilike(f"%{search}%"))

    query = query.order_by(Ticket.created_at.desc())
    result = await db.execute(query)
    rows = result.all()
    return [_ticket_to_list_response(ticket, employee_name=name) for ticket, name in rows]


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get ticket details. Employees can only view their own tickets."""
    result = await db.execute(
        select(Ticket, User.name)
        .join(User, Ticket.employee_id == User.id)
        .where(Ticket.id == ticket_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket, employee_name = row

    # Employees can only view their own tickets
    if current_user.role == "employee" and ticket.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _ticket_to_response(ticket, employee_name=employee_name)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    current_user: Annotated[User, Depends(require_role("agent"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update ticket category/priority. Agent only. Creates audit log entries."""
    result = await db.execute(
        select(Ticket, User.name)
        .join(User, Ticket.employee_id == User.id)
        .where(Ticket.id == ticket_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket, employee_name = row

    # Create audit logs for changes
    if payload.current_category and payload.current_category != ticket.current_category:
        audit = AuditLog(
            ticket_id=ticket.id,
            agent_id=current_user.id,
            field="category",
            old_value=ticket.current_category or "None",
            new_value=payload.current_category,
        )
        db.add(audit)
        ticket.current_category = payload.current_category

    if payload.current_priority and payload.current_priority != ticket.current_priority:
        audit = AuditLog(
            ticket_id=ticket.id,
            agent_id=current_user.id,
            field="priority",
            old_value=ticket.current_priority or "None",
            new_value=payload.current_priority,
        )
        db.add(audit)
        ticket.current_priority = payload.current_priority

    await db.flush()
    await db.refresh(ticket)

    return _ticket_to_response(ticket, employee_name=employee_name)


@router.post("/{ticket_id}/reply", response_model=TicketResponse)
async def reply_to_ticket(
    ticket_id: str,
    payload: TicketReply,
    current_user: Annotated[User, Depends(require_role("agent"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send a reply to a ticket and resolve it. Agent only."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(Ticket, User.name)
        .join(User, Ticket.employee_id == User.id)
        .where(Ticket.id == ticket_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket, employee_name = row

    if ticket.status == "resolved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is already resolved")

    ticket.final_reply = payload.final_reply
    ticket.status = "resolved"
    ticket.resolved_at = datetime.now(timezone.utc)
    ticket.resolved_by = current_user.id

    await db.flush()
    await db.refresh(ticket)

    response = _ticket_to_response(ticket, employee_name=employee_name)

    # Notify the specific employee who filed this ticket, so their
    # "My Tickets" view flips to Resolved live without a manual refresh.
    await manager.notify_employee(
        user_id=ticket.employee_id,
        event="ticket_resolved",
        data=response.model_dump(mode="json"),
    )

    return response


@router.get("/{ticket_id}/audit", response_model=list[AuditLogResponse])
async def get_ticket_audit(
    ticket_id: str,
    current_user: Annotated[User, Depends(require_role("agent"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get audit log for a ticket. Agent only."""
    # Verify ticket exists
    ticket_result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    if not ticket_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    result = await db.execute(
        select(AuditLog, User.name)
        .join(User, AuditLog.agent_id == User.id)
        .where(AuditLog.ticket_id == ticket_id)
        .order_by(AuditLog.created_at.desc())
    )
    rows = result.all()
    return [
        AuditLogResponse(
            id=log.id,
            ticket_id=log.ticket_id,
            agent_id=log.agent_id,
            agent_name=name,
            field=log.field,
            old_value=log.old_value,
            new_value=log.new_value,
            created_at=log.created_at,
        )
        for log, name in rows
    ]
