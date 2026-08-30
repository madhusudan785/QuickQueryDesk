"""Ticket SQLAlchemy model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Ticket(Base):
    """Ticket model for helpdesk support requests."""

    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AI-suggested values (original, immutable after initial classification)
    ai_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Current values (may be overridden by agents)
    current_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)

    # AI draft and final reply
    ai_draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    rag_sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Relationships
    employee = relationship("User", back_populates="tickets", foreign_keys=[employee_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    audit_logs = relationship("AuditLog", back_populates="ticket", cascade="all, delete-orphan")

    # Indexes for common query patterns
    __table_args__ = (
        Index("ix_tickets_employee_id", "employee_id"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_current_category", "current_category"),
        Index("ix_tickets_current_priority", "current_priority"),
    )

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, title={self.title}, status={self.status})>"
