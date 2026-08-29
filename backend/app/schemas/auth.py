"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(..., pattern="^(employee|agent)$")

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    name: str
