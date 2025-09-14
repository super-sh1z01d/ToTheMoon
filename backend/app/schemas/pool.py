"""
Pool related Pydantic schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class PoolBase(BaseModel):
    """
    Базовая схема пула ликвидности
    """
    pool_address: str = Field(
        ..., 
        min_length=32, 
        max_length=44,
        description="Адрес пула ликвидности в сети Solana"
    )
    dex_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Название DEX (raydium, orca, etc.)"
    )
    is_active: bool = Field(default=True, description="Активен ли пул для торгов")
    
    @field_validator('pool_address')
    def validate_pool_address(cls, v: str):
        """Валидация адреса пула Solana"""
        if not v or not isinstance(v, str):
            raise ValueError('Pool address must be a non-empty string')
        
        if len(v) < 32 or len(v) > 44:
            raise ValueError('Pool address length must be between 32 and 44 characters')
            
        return v
    
    @field_validator('dex_name')
    def validate_dex_name(cls, v: str):
        """Валидация названия DEX"""
        if not v or not isinstance(v, str):
            raise ValueError('DEX name must be a non-empty string')
        
        # Допустимые DEX
        allowed_dex = ['raydium', 'orca', 'jupiter', 'serum', 'aldrin', 'saros', 'mercurial']
        if v.lower() not in allowed_dex:
            raise ValueError(f'DEX name must be one of: {", ".join(allowed_dex)}')
            
        return v.lower()


class PoolCreate(PoolBase):
    """
    Схема для создания пула
    """
    token_id: str = Field(..., description="UUID токена, к которому относится пул")


class PoolUpdate(BaseModel):
    """
    Схема для обновления пула
    """
    dex_name: Optional[str] = Field(default=None, max_length=50, description="Название DEX")
    is_active: Optional[bool] = Field(default=None, description="Активен ли пул")


class PoolResponse(PoolBase):
    """
    Схема ответа с данными пула
    """
    id: str = Field(description="UUID пула")
    token_id: str = Field(description="UUID токена")
    created_at: datetime = Field(description="Время создания пула")
    updated_at: datetime = Field(description="Время последнего обновления")
    
    model_config = ConfigDict(from_attributes=True)
