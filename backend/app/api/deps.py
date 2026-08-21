from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


async def get_current_user() -> None:
    raise NotImplementedError


__all__ = ["AsyncSession", "get_current_user", "get_db"]
