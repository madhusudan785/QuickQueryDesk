"""Models package - import all models for Alembic discovery.

NOTE: This is the Part 1 (auth) commit. Ticket and AuditLog models
are added in Part 2 — this file will import them then too.
"""

from app.models.user import User

__all__ = ["User"]
