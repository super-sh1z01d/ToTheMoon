"""
Common Pydantic schemas
"""

from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Параметры пагинации для API endpoints
    """
    limit: int = Field(default=50, ge=1, le=1000, description="Количество элементов на странице")
    offset: int = Field(default=0, ge=0, description="Смещение от начала")


class PaginationResponse(BaseModel, Generic[T]):
    """
    Базовый ответ с пагинацией
    """
    items: List[T] = Field(description="Список элементов")
    total: int = Field(description="Общее количество элементов")
    limit: int = Field(description="Лимит элементов на странице")
    offset: int = Field(description="Смещение от начала")
    has_more: bool = Field(description="Есть ли еще элементы")


class HealthStatus(BaseModel):
    """
    Статус здоровья системы
    """
    status: str = Field(description="Общий статус системы")
    timestamp: int = Field(description="Временная метка проверки")
    services: dict = Field(description="Статус отдельных сервисов")


class ErrorResponse(BaseModel):
    """
    Стандартный ответ об ошибке
    """
    error: str = Field(description="Тип ошибки")
    message: str = Field(description="Описание ошибки")
    details: Optional[dict] = Field(default=None, description="Дополнительные детали ошибки")
