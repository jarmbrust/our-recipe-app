from __future__ import annotations

from typing import Any

from app.config import settings

AUTH_COOKIE_NAME = "access_token"
AUTH_COOKIE_MAX_AGE = 86400  # 24h — matches JWT expiry


def auth_cookie_settings() -> dict[str, Any]:
    """Shared Set-Cookie attributes for setting and clearing the auth cookie.

    Dev (localhost): no Domain, no Secure.
    Prod: Secure + Domain=.ourrecipeapp.com so app. and api. share the cookie.
    """
    attrs: dict[str, Any] = {"samesite": "lax", "path": "/", "httponly": True}
    if settings.ENV == "prod":
        attrs["secure"] = True
        attrs["domain"] = ".ourrecipeapp.com"
    return attrs
