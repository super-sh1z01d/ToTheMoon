"""
System related Pydantic schemas
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class SystemConfigResponse(BaseModel):
    """
    Схема ответа для системной конфигурации
    """
    config: Dict[str, Dict[str, Any]] = Field(description="Конфигурация по категориям")
    total_params: int = Field(description="Общее количество параметров")


class SystemConfigItemResponse(BaseModel):
    """
    Схема ответа для отдельного элемента конфигурации
    """
    id: str = Field(description="UUID параметра")
    key: str = Field(description="Ключ параметра")
    value: Any = Field(description="Значение параметра")
    description: Optional[str] = Field(default=None, description="Описание параметра")
    category: Optional[str] = Field(default=None, description="Категория параметра")
    created_at: datetime = Field(description="Время создания")
    updated_at: datetime = Field(description="Время последнего обновления")
    
    model_config = ConfigDict(from_attributes=True)


class SystemConfigUpdate(BaseModel):
    """
    Схема для обновления конфигурации
    """
    value: Any = Field(..., description="Новое значение параметра")
    description: Optional[str] = Field(default=None, description="Новое описание")


class SystemStatsResponse(BaseModel):
    """
    Схема ответа для статистики системы
    """
    total_tokens: int = Field(description="Общее количество токенов")
    by_status: Dict[str, int] = Field(description="Количество токенов по статусам")
    total_pools: int = Field(description="Общее количество пулов")
    active_pools: int = Field(description="Количество активных пулов")
    config_params: int = Field(description="Количество параметров конфигурации")


class AppInfoResponse(BaseModel):
    """
    Схема ответа для информации о приложении
    """
    name: str = Field(description="Название приложения")
    version: str = Field(description="Версия приложения")
    description: str = Field(description="Описание приложения")
    environment: str = Field(description="Окружение (development/production)")
    features: List[str] = Field(description="Список возможностей системы")
