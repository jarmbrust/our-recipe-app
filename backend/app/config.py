from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _split_csv(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(origin) for origin in value]
    return [origin.strip() for origin in str(value).split(",") if origin.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 1440
    ENV: Literal["dev", "prod"] = "dev"
    CORS_ORIGINS: Annotated[list[str], NoDecode, BeforeValidator(_split_csv)] = []


settings = Settings()
