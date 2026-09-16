from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    display_name: str | None = None
    about: str | None = None
    avatar_url: str | None = None
    created_at: datetime


class UserUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    about: str | None = None
    avatar_url: str | None = None


class EmailUpdateIn(BaseModel):
    email: EmailStr
    current_password: str


class PasswordUpdateIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
