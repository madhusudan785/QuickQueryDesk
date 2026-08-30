"""Pydantic schemas for tickets."""

from datetime import datetime
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    """Schema for creating a new ticket."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    attachment_filename: str | None = Field(None, max_length=255)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class TicketUpdate(BaseModel):
    """Schema for agent updating ticket category/priority."""
    current_category: str | None = Field(None, pattern="^(IT|HR|Finance|Admin|Other)$")
    current_priority: str | None = Field(None, pattern="^(Low|Medium|High)$")

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class TicketReply(BaseModel):
    """Schema for agent sending a reply to resolve a ticket."""
    final_reply: str = Field(..., min_length=1)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class TicketResponse(BaseModel):
    """Schema for ticket data in API responses."""
    id: str
    employee_id: str
    employee_name: str | None = None
    title: str
    description: str
    attachment_filename: str | None
    ai_category: str | None
    current_category: str | None
    ai_priority: str | None
    current_priority: str | None
    status: str
    ai_draft_reply: str | None
    final_reply: str | None
    rag_sources: list[dict] | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    """Schema for ticket list items (lighter than full response)."""
    id: str
    title: str
    current_category: str | None
    current_priority: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    employee_name: str | None = None

    model_config = {"from_attributes": True}
