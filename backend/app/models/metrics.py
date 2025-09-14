"""
Token metrics and scoring models
"""

from decimal import Decimal
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class TokenMetrics(BaseModel):
    """
    Исторические метрики токенов (временные ряды)
    Партиционируется по дням для производительности
    """
    __tablename__ = "token_metrics"
    
    # Связь с токеном
    token_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Временная метка (ключ партиционирования)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Время снятия метрик"
    )
    
    # Транзакции
    tx_count_5m = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество транзакций за 5 минут"
    )
    
    tx_count_1h = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество транзакций за 1 час"
    )
    
    # Объемы торгов в USD
    volume_5m_usd = Column(
        Numeric(precision=20, scale=2),
        nullable=False,
        default=0,
        comment="Объем торгов за 5 минут в USD"
    )
    
    volume_1h_usd = Column(
        Numeric(precision=20, scale=2),
        nullable=False,
        default=0,
        comment="Объем торгов за 1 час в USD"
    )
    
    # Объемы покупок/продаж (для дисбаланса)
    buys_volume_5m_usd = Column(
        Numeric(precision=20, scale=2),
        nullable=False,
        default=0,
        comment="Объем покупок за 5 минут в USD"
    )
    
    sells_volume_5m_usd = Column(
        Numeric(precision=20, scale=2),
        nullable=False,
        default=0,
        comment="Объем продаж за 5 минут в USD"
    )
    
    # Холдеры
    holders_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество держателей токена"
    )
    
    # Ликвидность
    liquidity_usd = Column(
        Numeric(precision=20, scale=2),
        nullable=False,
        default=0,
        comment="Общая ликвидность в USD"
    )
    
    # Связи
    token = relationship("Token", back_populates="metrics")
    
    # Индексы для временных рядов и партиционирования
    __table_args__ = (
        Index("ix_token_metrics_token_time", "token_id", "timestamp"),
        Index("ix_token_metrics_timestamp", "timestamp"),  # Для партиционирования
        Index("ix_token_metrics_volume", "volume_5m_usd", "timestamp"),
        Index("ix_token_metrics_tx_count", "tx_count_5m", "timestamp"),
        
        # Партиционирование по дням будет добавлено в миграции
        # PARTITION BY RANGE (timestamp)
    )
    
    def __repr__(self) -> str:
        return f"<TokenMetrics(token_id={str(self.token_id)[:8]}..., timestamp={self.timestamp})>"


class TokenScores(BaseModel):
    """
    История расчетов скоров токенов
    """
    __tablename__ = "token_scores"
    
    # Связь с токеном
    token_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Модель скоринга
    model_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Название модели скоринга (например, hybrid_momentum_v1)"
    )
    
    # Результат скоринга
    score_value = Column(
        Float,
        nullable=False,
        comment="Значение скора"
    )
    
    # Временная метка
    calculated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Время расчета скора"
    )
    
    # Детали расчета (JSONB для гибкости)
    components = Column(
        JSONB,
        nullable=True,
        comment="Детали расчета компонентов скора в JSON"
    )
    
    # Связи
    token = relationship("Token", back_populates="scores")
    
    # Индексы для аналитики и производительности
    __table_args__ = (
        Index("ix_token_scores_token_calculated", "token_id", "calculated_at"),
        Index("ix_token_scores_model_calculated", "model_name", "calculated_at"),
        Index("ix_token_scores_value_calculated", "score_value", "calculated_at"),
        Index("ix_token_scores_model_score", "model_name", "score_value"),
    )
    
    def __repr__(self) -> str:
        return f"<TokenScores(token_id={str(self.token_id)[:8]}..., model={self.model_name}, score={self.score_value})>"
