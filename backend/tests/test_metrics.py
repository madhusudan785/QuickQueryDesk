"""Tests for the metrics API endpoint.

These tests verify auth, status counts, category distribution,
median resolution time, and AI override percentage.

Seed data is inserted/cleaned via raw asyncpg (bypassing the app's
SQLAlchemy engine which is bound to a different event loop).
"""

import uuid
from datetime import datetime, timedelta, timezone

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.core.config import get_settings
from app.main import app

settings = get_settings()
# Convert SQLAlchemy URL to raw asyncpg DSN
_DSN = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


def _agent_headers(user_id: str) -> dict[str, str]:
    """Return Authorization header for an agent."""
    token = create_access_token({"sub": user_id, "role": "agent"})
    return {"Authorization": f"Bearer {token}"}


def _employee_headers(user_id: str) -> dict[str, str]:
    """Return Authorization header for an employee."""
    token = create_access_token({"sub": user_id, "role": "employee"})
    return {"Authorization": f"Bearer {token}"}


async def _seed(suffix: str) -> dict[str, str]:
    """Insert test users + tickets via asyncpg."""
    agent_id = f"mt-agent-{suffix}"
    emp_id = f"mt-emp-{suffix}"
    now = datetime.now(timezone.utc)

    conn = await asyncpg.connect(_DSN)
    try:
        await conn.execute(
            "INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES "
            "($1, 'Test Agent', $2, 'x', 'agent', $3), "
            "($4, 'Test Employee', $5, 'x', 'employee', $3)",
            agent_id, f"{agent_id}@t.com", now,
            emp_id, f"{emp_id}@t.com",
        )

        # t1: IT open
        await conn.execute(
            "INSERT INTO tickets "
            "(id, employee_id, title, description, ai_category, current_category, "
            " ai_priority, current_priority, status, created_at, updated_at) VALUES "
            "($1, $2, 'T1', 'd', 'IT', 'IT', 'High', 'High', 'open', $3, $3)",
            f"t1-{suffix}", emp_id, now,
        )
        # t2: HR→Finance override, resolved 2h
        await conn.execute(
            "INSERT INTO tickets "
            "(id, employee_id, title, description, ai_category, current_category, "
            " ai_priority, current_priority, status, created_at, updated_at, resolved_at, resolved_by) VALUES "
            "($1, $2, 'T2', 'd', 'HR', 'Finance', 'Low', 'Low', 'resolved', $3, $4, $4, $5)",
            f"t2-{suffix}", emp_id, now - timedelta(hours=4), now - timedelta(hours=2), agent_id,
        )
        # t3: Finance kept, resolved 6h
        await conn.execute(
            "INSERT INTO tickets "
            "(id, employee_id, title, description, ai_category, current_category, "
            " ai_priority, current_priority, status, created_at, updated_at, resolved_at, resolved_by) VALUES "
            "($1, $2, 'T3', 'd', 'Finance', 'Finance', 'Medium', 'Medium', 'resolved', $3, $4, $4, $5)",
            f"t3-{suffix}", emp_id, now - timedelta(hours=8), now - timedelta(hours=2), agent_id,
        )
        # t4: No AI category (fallback), open
        await conn.execute(
            "INSERT INTO tickets "
            "(id, employee_id, title, description, current_category, "
            " current_priority, status, created_at, updated_at) VALUES "
            "($1, $2, 'T4', 'd', 'Other', 'Medium', 'open', $3, $3)",
            f"t4-{suffix}", emp_id, now,
        )
    finally:
        await conn.close()

    return {"agent_id": agent_id, "emp_id": emp_id, "suffix": suffix}


async def _cleanup(suffix: str, emp_id: str, agent_id: str) -> None:
    """Remove seeded test data via asyncpg."""
    conn = await asyncpg.connect(_DSN)
    try:
        await conn.execute("DELETE FROM tickets WHERE employee_id = $1", emp_id)
        await conn.execute("DELETE FROM users WHERE id = $1 OR id = $2", agent_id, emp_id)
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_metrics_requires_auth():
    """Unauthenticated request to /metrics should return 403."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/metrics")
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_metrics_employee_forbidden():
    """Employee users should receive 403 from /metrics."""
    s = uuid.uuid4().hex[:6]
    data = await _seed(s)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/metrics", headers=_employee_headers(data["emp_id"]))
            assert resp.status_code == 403
    finally:
        await _cleanup(s, data["emp_id"], data["agent_id"])


@pytest.mark.asyncio
async def test_metrics_agent_success():
    """Agent users should receive 200 with correct metrics shape."""
    s = uuid.uuid4().hex[:6]
    data = await _seed(s)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/metrics", headers=_agent_headers(data["agent_id"]))
            assert resp.status_code == 200

            body = resp.json()
            for key in ("status_counts", "category_distribution",
                        "median_resolution_hours", "ai_override_percentage",
                        "total_tickets", "total_classified", "total_overridden"):
                assert key in body
    finally:
        await _cleanup(s, data["emp_id"], data["agent_id"])


@pytest.mark.asyncio
async def test_metrics_status_counts():
    """Status counts should include seeded open and resolved tickets."""
    s = uuid.uuid4().hex[:6]
    data = await _seed(s)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/metrics", headers=_agent_headers(data["agent_id"]))
            body = resp.json()

            assert body["status_counts"]["open"] >= 2
            assert body["status_counts"]["resolved"] >= 2
    finally:
        await _cleanup(s, data["emp_id"], data["agent_id"])


@pytest.mark.asyncio
async def test_metrics_category_counts():
    """All five standard categories should be present in the response."""
    s = uuid.uuid4().hex[:6]
    data = await _seed(s)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/metrics", headers=_agent_headers(data["agent_id"]))
            body = resp.json()
            dist = body["category_distribution"]

            for cat in ["IT", "HR", "Finance", "Admin", "Other"]:
                assert cat in dist
                assert isinstance(dist[cat], int)

            assert dist["Finance"] >= 2
            assert dist["IT"] >= 1
            assert dist["Other"] >= 1
    finally:
        await _cleanup(s, data["emp_id"], data["agent_id"])


@pytest.mark.asyncio
async def test_metrics_median_resolution_with_resolved():
    """Median resolution should be a positive number when resolved tickets exist."""
    s = uuid.uuid4().hex[:6]
    data = await _seed(s)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/metrics", headers=_agent_headers(data["agent_id"]))
            body = resp.json()

            assert body["median_resolution_hours"] is not None
            assert body["median_resolution_hours"] > 0
    finally:
        await _cleanup(s, data["emp_id"], data["agent_id"])


@pytest.mark.asyncio
async def test_metrics_median_resolution_type():
    """Median resolution hours should be float, int, or null."""
    s = uuid.uuid4().hex[:6]
    data = await _seed(s)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/metrics", headers=_agent_headers(data["agent_id"]))
            body = resp.json()
            assert isinstance(body["median_resolution_hours"], (float, int, type(None)))
    finally:
        await _cleanup(s, data["emp_id"], data["agent_id"])


@pytest.mark.asyncio
async def test_metrics_ai_override_percentage():
    """AI override percentage should be correctly calculated.

    Seeded data: 3 tickets with ai_category set, 1 overridden (HR→Finance).
    Expected: at least 1 override out of at least 3 classified.
    """
    s = uuid.uuid4().hex[:6]
    data = await _seed(s)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/metrics", headers=_agent_headers(data["agent_id"]))
            body = resp.json()

            assert isinstance(body["ai_override_percentage"], (float, int))
            assert 0 <= body["ai_override_percentage"] <= 100
            assert body["total_classified"] >= 3
            assert body["total_overridden"] >= 1
    finally:
        await _cleanup(s, data["emp_id"], data["agent_id"])
