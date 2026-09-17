from __future__ import annotations

import os

# Must be set before importing app modules — settings are read at import time.
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/recipe_app_test"
os.environ["JWT_SECRET"] = "test-secret-at-least-32-bytes-long-1234567890"
os.environ["ENV"] = "dev"

from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: E402, F401  (registers models on Base.metadata)
from app.db.base import Base  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _prepare_test_db() -> AsyncIterator[None]:
    """Fresh schema per test, isolated from the dev database (port 5433)."""
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield
