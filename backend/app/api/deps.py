from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.cookies import AUTH_COOKIE_NAME
from app.services.security import decode_access_token

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(request: Request, session: DbSession) -> User:
    """Resolve the authenticated user from the JWT cookie; raise 401 otherwise."""
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(token)  # raises 401 on invalid/expired
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = await session.get(User, int(sub))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

__all__ = ["AsyncSession", "CurrentUser", "DbSession", "get_current_user", "get_db"]
