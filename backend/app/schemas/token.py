"""
Token related Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.token import TokenStatus


class TokenBase(BaseModel):
    """
    Базовая схема токена
    """
    token_address: str = Field(
        ..., 
        min_length=32, 
        max_length=44,
        description="Адрес контракта токена в сети Solana"
    )
    
    @field_validator('token_address')
    def validate_token_address(cls, v: str):
        """Валидация адреса токена Solana"""
        if not v or not isinstance(v, str):
            raise ValueError('Token address must be a non-empty string')
        
        # Базовая валидация для Solana адреса (base58)
        if len(v) < 32 or len(v) > 44:
            raise ValueError('Token address length must be between 32 and 44 characters')
            
        return v


class TokenCreate(TokenBase):
    """
    Схема для создания токена
    """
    pass


class TokenUpdate(BaseModel):
    """
    Схема для обновления токена
    """
    status: Optional[TokenStatus] = Field(default=None, description="Новый статус токена")
    last_score_value: Optional[float] = Field(default=None, description="Новое значение скора")


class TokenResponse(TokenBase):
    """
    Схема ответа с данными токена
    """
    id: str = Field(description="UUID токена")
    status: TokenStatus = Field(description="Текущий статус токена")
    created_at: datetime = Field(description="Время создания токена")
    updated_at: datetime = Field(description="Время последнего обновления")
    activated_at: Optional[datetime] = Field(default=None, description="Время активации")
    archived_at: Optional[datetime] = Field(default=None, description="Время архивации")
    last_score_value: Optional[float] = Field(default=None, description="Последнее значение скора")
    last_score_calculated_at: Optional[datetime] = Field(default=None, description="Время последнего расчета скора")
    pools_count: Optional[int] = Field(default=None, description="Количество пулов токена")
    
    model_config = ConfigDict(from_attributes=True)


class TokenListResponse(BaseModel):
    """
    Схема ответа со списком токенов
    """
    tokens: List[TokenResponse] = Field(description="Список токенов")
    total: int = Field(description="Общее количество токенов")
    limit: int = Field(description="Лимит элементов на странице")
    offset: int = Field(description="Смещение от начала")
    has_more: bool = Field(description="Есть ли еще токены")


class TokenStatusHistoryResponse(BaseModel):
    """
    Схема для истории изменений статуса токена
    """
    id: str = Field(description="UUID записи истории")
    old_status: Optional[TokenStatus] = Field(description="Предыдущий статус")
    new_status: TokenStatus = Field(description="Новый статус")
    reason: str = Field(description="Причина изменения статуса")
    changed_at: datetime = Field(description="Время изменения")
    change_metadata: Optional[str] = Field(default=None, description="Дополнительная информация")
    
    model_config = ConfigDict(from_attributes=True)
