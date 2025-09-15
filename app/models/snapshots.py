from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TokenSnapshot(Base):
    __tablename__ = "token_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(nullable=False)
    holders: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)

    token: Mapped["Token"] = relationship(back_populates="snapshots")


class PoolSnapshot(Base):
    __tablename__ = "pool_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("pools.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(nullable=False)
    liquidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    tx_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    buys_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    sells_volume: Mapped[float | None] = mapped_column(Float, nullable=True)

    pool: Mapped["Pool"] = relationship(back_populates="snapshots")

