from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (auto-generated salt)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time check of a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Malformed hash or password over bcrypt's 72-byte limit.
        return False


def create_access_token(sub: int, expires_delta: timedelta | None = None) -> str:
    """Issue a JWT with `sub` = user id and `exp` per settings (default 24h)."""
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRES_MINUTES))
    payload = {"sub": str(sub), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, object]:
    """Decode and verify a JWT; raise 401 on any failure."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None
