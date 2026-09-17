from __future__ import annotations

from sqlalchemy import BigInteger, Identity, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False)
    system: Mapped[str] = mapped_column(String(20), nullable=False)  # "metric" | "imperial"
