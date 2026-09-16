from __future__ import annotations

import httpx
from httpx import ASGITransport

from app.main import app
from app.services.cookies import AUTH_COOKIE_NAME

BASE_URL = "http://test"


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL)


async def register(
    client: httpx.AsyncClient,
    username: str = "thechef",
    email: str = "chef@example.com",
    password: str = "securePassword123",
    display_name: str = "James da Chef",
) -> httpx.Response:
    return await client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )


async def test_register_success() -> None:
    async with make_client() as client:
        res = await register(client)
        assert res.status_code == 201

        body = res.json()
        assert body["username"] == "thechef"
        assert body["email"] == "chef@example.com"
        assert "password_hash" not in body

        set_cookie = res.headers["set-cookie"]
        assert AUTH_COOKIE_NAME in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie
        # dev env: no Domain, no Secure
        assert "Domain=" not in set_cookie
        assert "Secure" not in set_cookie


async def test_register_duplicate_username() -> None:
    async with make_client() as client:
        await register(client)
        res = await register(client, email="other@example.com")
        assert res.status_code == 409


async def test_register_duplicate_email() -> None:
    async with make_client() as client:
        await register(client)
        res = await register(client, username="otherchef")
        assert res.status_code == 409


async def test_login_wrong_password() -> None:
    async with make_client() as client:
        await register(client)
        res = await client.post(
            "/api/auth/login",
            json={"username": "thechef", "password": "wrong-password-1"},
        )
        assert res.status_code == 401


async def test_get_user_requires_auth() -> None:
    async with make_client() as client:
        res = await client.get("/api/auth/user")
        assert res.status_code == 401


async def test_get_user_with_cookie() -> None:
    async with make_client() as client:
        await register(client)
        res = await client.get("/api/auth/user")
        assert res.status_code == 200
        body = res.json()
        assert body["username"] == "thechef"
        assert "password_hash" not in body


async def test_logout_clears_cookie() -> None:
    async with make_client() as client:
        await register(client)
        res = await client.post("/api/auth/logout")
        assert res.status_code == 200
        set_cookie = res.headers["set-cookie"]
        assert AUTH_COOKIE_NAME in set_cookie
        assert "Max-Age=0" in set_cookie
