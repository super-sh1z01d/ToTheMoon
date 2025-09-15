from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Pool(Base):
    __tablename__ = "pools"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False)
    pool_address: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    dex_name: Mapped[str] = mapped_column(String, nullable=False)

    token: Mapped["Token"] = relationship(back_populates="pools")
    snapshots: Mapped[list["PoolSnapshot"]] = relationship(back_populates="pool", cascade="all, delete-orphan")

