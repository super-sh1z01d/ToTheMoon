"""
Token related models
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import BaseModel


class TokenStatus(enum.Enum):
    """
    Статусы токена в системе
    """
    INITIAL = "initial"      # Начальный мониторинг
    ACTIVE = "active"        # Активный скоринг  
    ARCHIVED = "archived"    # Исключен из мониторинга


class StatusChangeReason(enum.Enum):
    """
    Причины смены статуса токена
    """
    DISCOVERY = "discovery"           # Обнаружен через WebSocket
    ACTIVATION = "activation"         # Выполнены условия активации
    LOW_SCORE = "low_score"          # Низкий скор длительное время
    LOW_ACTIVITY = "low_activity"     # Низкая активность в пулах
    ARCHIVAL_TIMEOUT = "archival_timeout"  # Таймаут в initial статусе


class Token(BaseModel):
    """
    Основная сущность токена Solana
    """
    __tablename__ = "tokens"
    
    # Основные поля
    token_address = Column(
        String(44),  # Solana адреса фиксированной длины
        unique=True, 
        nullable=False,
        index=True,
        comment="Адрес контракта токена в сети Solana"
    )
    
    status = Column(
        Enum(TokenStatus),
        nullable=False,
        default=TokenStatus.INITIAL,
        index=True,
        comment="Текущий статус токена в системе"
    )
    
    # Временные метки жизненного цикла
    activated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время перехода в статус Active"
    )
    
    archived_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время перехода в статус Archived"
    )
    
    # Скоринг
    last_score_value = Column(
        Float,
        nullable=True,
        comment="Последнее значение скора"
    )
    
    last_score_calculated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время последнего расчета скора"
    )
    
    # Связи
    pools = relationship("Pool", back_populates="token", cascade="all, delete-orphan")
    status_history = relationship("TokenStatusHistory", back_populates="token", cascade="all, delete-orphan")
    metrics = relationship("TokenMetrics", back_populates="token", cascade="all, delete-orphan")
    scores = relationship("TokenScores", back_populates="token", cascade="all, delete-orphan")
    
    # Индексы для производительности
    __table_args__ = (
        Index("ix_tokens_status_created", "status", "created_at"),
        Index("ix_tokens_score_active", "last_score_value", "status"),
        Index("ix_tokens_address_status", "token_address", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Token(address={self.token_address[:8]}..., status={self.status.value})>"


class TokenStatusHistory(BaseModel):
    """
    История изменений статусов токенов для аналитики
    """
    __tablename__ = "token_status_history"
    
    # Связь с токеном
    token_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Изменения статуса
    old_status = Column(
        Enum(TokenStatus),
        nullable=True,  # NULL для первого создания
        comment="Предыдущий статус"
    )
    
    new_status = Column(
        Enum(TokenStatus),
        nullable=False,
        comment="Новый статус"
    )
    
    reason = Column(
        Enum(StatusChangeReason),
        nullable=False,
        comment="Причина смены статуса"
    )
    
    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Время изменения статуса"
    )
    
    # Дополнительные данные (JSON)
    change_metadata = Column(
        String,  # Простая строка вместо JSONB для простоты
        nullable=True,
        comment="Дополнительная информация об изменении"
    )
    
    # Связи
    token = relationship("Token", back_populates="status_history")
    
    # Индексы
    __table_args__ = (
        Index("ix_status_history_token_time", "token_id", "changed_at"),
        Index("ix_status_history_reason", "reason", "changed_at"),
        Index("ix_status_history_new_status", "new_status", "changed_at"),
    )
    
    def __repr__(self) -> str:
        return f"<TokenStatusHistory(token_id={str(self.token_id)[:8]}..., {self.old_status} -> {self.new_status})>"
