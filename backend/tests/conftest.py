"""Shared test configuration for async database tests.

The app creates its SQLAlchemy async engine at module-import time which
binds the asyncpg pool to an event loop that no longer exists when
pytest-asyncio creates a new loop for each test. This conftest replaces
the engine with a fresh one on the current event loop before each test.
"""

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings
from app.database import session as db_module

settings = get_settings()


@pytest_asyncio.fixture(autouse=True)
async def _fresh_engine():
    """Replace the module-level engine with one on the current event loop."""
    new_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    new_factory = async_sessionmaker(
        new_engine, class_=AsyncSession, expire_on_commit=False,
    )

    # Monkey-patch the module-level references so the app uses our engine
    old_engine = db_module.engine
    old_factory = db_module.async_session_factory

    db_module.engine = new_engine
    db_module.async_session_factory = new_factory

    yield

    # Restore and clean up
    await new_engine.dispose()
    db_module.engine = old_engine
    db_module.async_session_factory = old_factory
