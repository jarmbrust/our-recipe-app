from __future__ import annotations

from fastapi import APIRouter, Request

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    return {
        "status": "ok",
        "version": request.app.version,
        "env": settings.ENV,
    }
