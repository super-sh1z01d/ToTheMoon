"""
System configuration models
"""

from sqlalchemy import Column, String, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import BaseModel


class SystemConfig(BaseModel):
    """
    Конфигурация системы для hot reload параметров
    """
    __tablename__ = "system_config"
    
    # Ключ конфигурации
    key = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Ключ конфигурационного параметра"
    )
    
    # Значение в JSON формате для гибкости
    value = Column(
        JSONB,
        nullable=False,
        comment="Значение параметра в JSON формате"
    )
    
    # Описание параметра
    description = Column(
        String(500),
        nullable=True,
        comment="Описание назначения параметра"
    )
    
    # Категория для группировки в админке
    category = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Категория параметра (scoring, limits, etc.)"
    )
    
    # Индексы
    __table_args__ = (
        Index("ix_system_config_category_key", "category", "key"),
    )
    
    def __repr__(self) -> str:
        return f"<SystemConfig(key={self.key}, category={self.category})>"
