"""
Liquidity pool models
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Pool(BaseModel):
    """
    Пул ликвидности токена на DEX
    """
    __tablename__ = "pools"
    
    # Основные поля
    pool_address = Column(
        String(44),  # Solana адреса фиксированной длины
        unique=True,
        nullable=False,
        index=True,
        comment="Адрес пула ликвидности"
    )
    
    # Связь с токеном
    token_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # DEX информация
    dex_name = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Название DEX (raydium, orca, etc.)"
    )
    
    # Статус пула
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Активен ли пул для торгов"
    )
    
    # Связи
    token = relationship("Token", back_populates="pools")
    
    # Индексы для производительности
    __table_args__ = (
        Index("ix_pools_token_active", "token_id", "is_active"),
        Index("ix_pools_dex_active", "dex_name", "is_active"),
        Index("ix_pools_address_token", "pool_address", "token_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Pool(address={self.pool_address[:8]}..., dex={self.dex_name}, active={self.is_active})>"
