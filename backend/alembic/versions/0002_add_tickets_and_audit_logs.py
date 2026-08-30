"""add tickets and audit_logs tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("attachment_filename", sa.String(255), nullable=True),
        sa.Column("ai_category", sa.String(50), nullable=True),
        sa.Column("ai_priority", sa.String(20), nullable=True),
        sa.Column("current_category", sa.String(50), nullable=True),
        sa.Column("current_priority", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("ai_draft_reply", sa.Text, nullable=True),
        sa.Column("final_reply", sa.Text, nullable=True),
        sa.Column("rag_sources", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_tickets_employee_id", "tickets", ["employee_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_current_category", "tickets", ["current_category"])
    op.create_index("ix_tickets_current_priority", "tickets", ["current_priority"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ticket_id", sa.String(36), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field", sa.String(50), nullable=False),
        sa.Column("old_value", sa.String(100), nullable=False),
        sa.Column("new_value", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_ticket_id", "audit_logs", ["ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_ticket_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_tickets_current_priority", table_name="tickets")
    op.drop_index("ix_tickets_current_category", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_employee_id", table_name="tickets")
    op.drop_table("tickets")
