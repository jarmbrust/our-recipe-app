from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.auth import (
    EmailUpdateIn,
    LoginIn,
    PasswordUpdateIn,
    RegisterIn,
    UserOut,
    UserUpdateIn,
)
from app.services.cookies import AUTH_COOKIE_MAX_AGE, AUTH_COOKIE_NAME, auth_cookie_settings
from app.services.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register(payload: RegisterIn, response: Response, session: DbSession) -> User:
    """Create an account and auto-login (sets the JWT cookie)."""
    existing = await session.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email),
        ),
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        display_name=payload.display_name or payload.username,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(sub=user.id)
    response.set_cookie(
        AUTH_COOKIE_NAME,
        token,
        max_age=AUTH_COOKIE_MAX_AGE,
        **auth_cookie_settings(),
    )
    return user


@router.post("/login", response_model=UserOut)
async def login(payload: LoginIn, response: Response, session: DbSession) -> User:
    """Authenticate and set the JWT cookie."""
    user = await session.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(sub=user.id)
    response.set_cookie(
        AUTH_COOKIE_NAME,
        token,
        max_age=AUTH_COOKIE_MAX_AGE,
        **auth_cookie_settings(),
    )
    return user


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Clear the JWT cookie."""
    response.delete_cookie(AUTH_COOKIE_NAME, **auth_cookie_settings())
    return {"message": "Logged out"}


@router.get("/user", response_model=UserOut)
async def get_user(user: CurrentUser) -> User:
    """Return the current user's profile."""
    return user


@router.put("/user")
async def update_user(payload: UserUpdateIn, user: CurrentUser) -> dict[str, str]:
    """Stub (dev-steps Step 4): full behavior is a post-MVP follow-up."""
    return {"message": "Profile updated"}


@router.put("/email")
async def update_email(payload: EmailUpdateIn, user: CurrentUser) -> dict[str, str]:
    """Stub (dev-steps Step 4): full behavior is a post-MVP follow-up."""
    return {"message": "Email updated"}


@router.put("/password")
async def update_password(payload: PasswordUpdateIn, user: CurrentUser) -> dict[str, str]:
    """Stub (dev-steps Step 4): full behavior is a post-MVP follow-up."""
    return {"message": "Password updated"}
