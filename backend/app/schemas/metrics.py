"""Pydantic schemas for metrics."""

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    """Schema for the agent metrics dashboard response."""
    status_counts: dict[str, int]
    category_distribution: dict[str, int]
    median_resolution_hours: float | None
    ai_override_percentage: float
    total_tickets: int
    total_classified: int
    total_overridden: int
