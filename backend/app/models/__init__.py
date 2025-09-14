"""
SQLAlchemy models for ToTheMoon2
"""

# Импортируем все модели для Alembic автодискавери
from app.database import Base
from .token import Token, TokenStatusHistory
from .pool import Pool  
from .metrics import TokenMetrics, TokenScores
from .system import SystemConfig
from .raw_data import BirdeyeRawData

__all__ = [
    "Base",
    "Token", 
    "TokenStatusHistory",
    "Pool",
    "TokenMetrics",
    "TokenScores", 
    "SystemConfig",
    "BirdeyeRawData"
]
