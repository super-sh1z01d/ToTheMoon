from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Enum, Float, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TokenStatus(str, enum.Enum):
    INITIAL = "Initial"
    ACTIVE = "Active"
    ARCHIVED = "Archived"


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[TokenStatus] = mapped_column(Enum(TokenStatus, name="tokenstatus"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_score_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    pools: Mapped[list["Pool"]] = relationship(back_populates="token", cascade="all, delete-orphan")
    snapshots: Mapped[list["TokenSnapshot"]] = relationship(back_populates="token", cascade="all, delete-orphan")
    scores: Mapped[list["TokenScore"]] = relationship(back_populates="token", cascade="all, delete-orphan")
