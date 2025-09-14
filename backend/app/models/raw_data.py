"""
Raw data storage models
"""

from datetime import datetime, timedelta

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import BaseModel


class BirdeyeRawData(BaseModel):
    """
    Raw данные от Birdeye API с TTL для восстановления
    """
    __tablename__ = "birdeye_raw_data"
    
    # Адрес токена
    token_address = Column(
        String(44),
        nullable=False,
        index=True,
        comment="Адрес токена Solana"
    )
    
    # Тип endpoint'а
    endpoint = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Название API endpoint (token_overview, trades_info, etc.)"
    )
    
    # Raw данные от API
    response_data = Column(
        JSONB,
        nullable=False,
        comment="Полный ответ от Birdeye API в JSON"
    )
    
    # Временные метки для TTL
    fetched_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Время получения данных от API"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Время истечения данных (TTL = 7 дней)"
    )
    
    # Индексы для эффективного поиска и очистки
    __table_args__ = (
        Index("ix_birdeye_token_endpoint", "token_address", "endpoint"),
        Index("ix_birdeye_token_fetched", "token_address", "fetched_at"),
        Index("ix_birdeye_expires", "expires_at"),  # Для автоочистки
        Index("ix_birdeye_endpoint_fetched", "endpoint", "fetched_at"),
    )
    
    def __repr__(self) -> str:
        return f"<BirdeyeRawData(token={self.token_address[:8]}..., endpoint={self.endpoint})>"
    
    def is_expired(self) -> bool:
        """
        Проверка истечения срока действия данных
        """
        return datetime.now(self.expires_at.tzinfo) > self.expires_at
    
    @classmethod
    def create_with_ttl(cls, token_address: str, endpoint: str, response_data: dict, ttl_days: int = 7):
        """
        Создание записи с автоматическим TTL
        """
        now = datetime.now()
        expires_at = now + timedelta(days=ttl_days)
        
        return cls(
            token_address=token_address,
            endpoint=endpoint,
            response_data=response_data,
            expires_at=expires_at
        )
