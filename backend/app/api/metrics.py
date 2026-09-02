"""Metrics API routes — agent-only analytics dashboard."""

import statistics
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.metrics import MetricsResponse

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("", response_model=MetricsResponse)
async def get_metrics(
    current_user: Annotated[User, Depends(require_role("agent"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MetricsResponse:
    """Return aggregated ticket metrics for the agent dashboard.

    Metrics computed:
      - tickets by status (open / resolved)
      - tickets by category (IT, HR, Finance, Admin, Other)
      - median resolution time in hours (null if no resolved tickets)
      - AI category override percentage
    """

    # --- 1. Tickets by status (single query) ---
    status_rows = (
        await db.execute(
            select(Ticket.status, func.count()).group_by(Ticket.status)
        )
    ).all()
    status_counts: dict[str, int] = {"open": 0, "resolved": 0}
    total_tickets = 0
    for status_val, count in status_rows:
        status_counts[status_val] = count
        total_tickets += count

    # --- 2. Tickets by category (single query) ---
    # Group by the raw column and coalesce NULLs to "Other" in Python
    category_rows = (
        await db.execute(
            select(
                Ticket.current_category,
                func.count(),
            ).group_by(Ticket.current_category)
        )
    ).all()
    # Ensure all standard categories are present (even if zero)
    category_distribution: dict[str, int] = {
        "IT": 0, "HR": 0, "Finance": 0, "Admin": 0, "Other": 0,
    }
    for cat, count in category_rows:
        key = cat if cat else "Other"
        category_distribution[key] = category_distribution.get(key, 0) + count

    # --- 3. Median resolution time (resolved tickets only) ---
    resolved_rows = (
        await db.execute(
            select(Ticket.created_at, Ticket.resolved_at).where(
                Ticket.status == "resolved",
                Ticket.resolved_at.is_not(None),
            )
        )
    ).all()

    median_resolution_hours: float | None = None
    if resolved_rows:
        durations_hours = [
            (resolved_at - created_at).total_seconds() / 3600.0
            for created_at, resolved_at in resolved_rows
        ]
        median_resolution_hours = round(statistics.median(durations_hours), 2)

    # --- 4. AI category override percentage (single query) ---
    # Use SUM(CASE ...) for cross-version SQLAlchemy compatibility
    override_row = (
        await db.execute(
            select(
                func.sum(
                    case((Ticket.ai_category.is_not(None), 1), else_=0)
                ).label("total_classified"),
                func.sum(
                    case(
                        (
                            and_(
                                Ticket.ai_category.is_not(None),
                                Ticket.current_category != Ticket.ai_category,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("total_overridden"),
            )
        )
    ).one()
    total_classified: int = override_row.total_classified or 0
    total_overridden: int = override_row.total_overridden or 0
    ai_override_percentage = (
        round((total_overridden / total_classified) * 100, 1)
        if total_classified > 0
        else 0.0
    )

    return MetricsResponse(
        status_counts=status_counts,
        category_distribution=category_distribution,
        median_resolution_hours=median_resolution_hours,
        ai_override_percentage=ai_override_percentage,
        total_tickets=total_tickets,
        total_classified=total_classified,
        total_overridden=total_overridden,
    )

