"""Pydantic schemas for audit logs."""

from datetime import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Schema for audit log entries."""
    id: str
    ticket_id: str
    agent_id: str
    agent_name: str | None = None
    field: str
    old_value: str
    new_value: str
    created_at: datetime

    model_config = {"from_attributes": True}
