"""
Base model with common fields and utilities
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

# Base будет импортирован из database.py
from app.database import Base


class TimestampMixin:
    """
    Mixin для добавления timestamp полей
    """
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )


class BaseModel(Base, TimestampMixin):
    """
    Базовая модель с UUID primary key и timestamps
    """
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Конвертация модели в словарь для JSON сериализации
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
