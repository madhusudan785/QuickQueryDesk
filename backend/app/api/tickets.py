"""Ticket API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
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


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new support ticket. Employee only.
    
    The ticket is automatically classified by the Gemini LLM
    which suggests a category and priority level.
    """
    if current_user.role != "employee":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can create tickets")

    ticket = Ticket(
        employee_id=current_user.id,
        title=payload.title,
        description=payload.description,
        attachment_filename=payload.attachment_filename,
    )

    # AI-powered classification via Gemini LLM
    classification = await classify_ticket(payload.title, payload.description)
    ticket.ai_category = classification["category"]
    ticket.current_category = classification["category"]
    ticket.ai_priority = classification["priority"]
    ticket.current_priority = classification["priority"]

    # RAG: Retrieve relevant knowledge base articles
    query = f"{payload.title} {payload.description}"
    rag_sources = await retrieve_relevant_articles(query, top_k=3)
    ticket.rag_sources = [dict(s) for s in rag_sources] if rag_sources else None

    # Generate AI draft reply using RAG context
    draft_reply = await generate_draft_reply(
        title=payload.title,
        description=payload.description,
        category=classification["category"],
        priority=classification["priority"],
    )
    ticket.ai_draft_reply = draft_reply if draft_reply else None

    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

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

    # WebSocket notification will be added in Phase 10

    return _ticket_to_response(ticket, employee_name=employee_name)


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
