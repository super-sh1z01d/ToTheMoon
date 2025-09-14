"""
Modular scoring engine for ToTheMoon2
Модульная система скоринга токенов
"""

from .base import ScoringModelBase, ScoringResult, ScoringConfig
from .hybrid_momentum_v1 import HybridMomentumV1

# Доступные модели скоринга
AVAILABLE_MODELS = {
    "hybrid_momentum_v1": HybridMomentumV1,
    # Будущие модели будут добавлены здесь
    # "momentum_plus_v2": MomentumPlusV2,
    # "ml_prediction_v1": MLPredictionV1,
}

# Импортируем manager после определения AVAILABLE_MODELS
from .manager import ScoringManager

__all__ = [
    "ScoringModelBase",
    "ScoringResult", 
    "ScoringConfig",
    "HybridMomentumV1",
    "ScoringManager",
    "AVAILABLE_MODELS"
]
