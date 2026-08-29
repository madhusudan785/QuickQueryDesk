"""Pydantic schemas for users."""

from datetime import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    """Schema for user data in API responses."""
    id: str
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
