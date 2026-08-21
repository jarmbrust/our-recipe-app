from __future__ import annotations

import logging
import sys

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import health
from app.config import settings


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelname
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


logging.getLogger().handlers = [_InterceptHandler()]
logger.configure(handlers=[{"sink": sys.stdout, "serialize": True}])

app = FastAPI(title="Recipe API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)

app.include_router(api_router)
