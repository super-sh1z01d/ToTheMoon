"""
Base classes for scoring models
Базовые классы для моделей скоринга
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


@dataclass
class TokenMetricsInput:
    """
    Входные данные для расчета скора
    """
    # Транзакции
    tx_count_5m: int
    tx_count_1h: int
    
    # Объемы торгов
    volume_5m_usd: Decimal
    volume_1h_usd: Decimal
    buys_volume_5m_usd: Decimal
    sells_volume_5m_usd: Decimal
    
    # Держатели
    holders_count: int
    
    # Ликвидность
    liquidity_usd: Decimal
    
    # Временная метка
    timestamp: datetime
    
    # Держатели час назад (опциональное поле в конце)
    holders_1h_ago: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "tx_count_5m": self.tx_count_5m,
            "tx_count_1h": self.tx_count_1h,
            "volume_5m_usd": float(self.volume_5m_usd),
            "volume_1h_usd": float(self.volume_1h_usd),
            "buys_volume_5m_usd": float(self.buys_volume_5m_usd),
            "sells_volume_5m_usd": float(self.sells_volume_5m_usd),
            "holders_count": self.holders_count,
            "holders_1h_ago": self.holders_1h_ago,
            "liquidity_usd": float(self.liquidity_usd),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ScoringComponents:
    """
    Компоненты скоринга для модели Гибридный импульс
    """
    tx_accel: float = 0.0
    vol_momentum: float = 0.0
    holder_growth: float = 0.0
    orderflow_imbalance: float = 0.0
    
    # Сглаженные значения через EWMA
    tx_accel_smoothed: float = 0.0
    vol_momentum_smoothed: float = 0.0
    holder_growth_smoothed: float = 0.0
    orderflow_imbalance_smoothed: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Преобразование в словарь"""
        return {
            "tx_accel": self.tx_accel,
            "vol_momentum": self.vol_momentum,
            "holder_growth": self.holder_growth,
            "orderflow_imbalance": self.orderflow_imbalance,
            "tx_accel_smoothed": self.tx_accel_smoothed,
            "vol_momentum_smoothed": self.vol_momentum_smoothed,
            "holder_growth_smoothed": self.holder_growth_smoothed,
            "orderflow_imbalance_smoothed": self.orderflow_imbalance_smoothed
        }


@dataclass
class ScoringWeights:
    """
    Весовые коэффициенты для скоринга
    """
    W_tx: float = 0.25      # Вес ускорения транзакций
    W_vol: float = 0.35     # Вес импульса объема
    W_hld: float = 0.20     # Вес роста держателей
    W_oi: float = 0.20      # Вес дисбаланса потока ордеров
    
    def validate(self) -> bool:
        """Проверка что сумма весов = 1.0"""
        total = self.W_tx + self.W_vol + self.W_hld + self.W_oi
        return abs(total - 1.0) < 0.001
    
    def to_dict(self) -> Dict[str, float]:
        """Преобразование в словарь"""
        return {
            "W_tx": self.W_tx,
            "W_vol": self.W_vol,
            "W_hld": self.W_hld,
            "W_oi": self.W_oi
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'ScoringWeights':
        """Создание из словаря"""
        return cls(
            W_tx=data.get("W_tx", 0.25),
            W_vol=data.get("W_vol", 0.35),
            W_hld=data.get("W_hld", 0.20),
            W_oi=data.get("W_oi", 0.20)
        )


class ScoringConfig(BaseModel):
    """
    Конфигурация для скоринга
    """
    model_name: str = Field(description="Название модели скоринга")
    weights: Dict[str, float] = Field(description="Весовые коэффициенты")
    ewma_alpha: float = Field(default=0.3, ge=0.0, le=1.0, description="Параметр EWMA сглаживания")
    min_score_threshold: float = Field(default=0.5, description="Минимальный порог скора")
    
    model_config = ConfigDict(
        protected_namespaces=(),  # Отключаем защищенные namespace
        json_encoders={Decimal: float},
    )


@dataclass
class ScoringResult:
    """
    Результат расчета скора
    """
    token_address: str
    model_name: str
    score_value: float
    score_smoothed: float  # Сглаженный скор через EWMA
    components: ScoringComponents
    weights: ScoringWeights
    timestamp: datetime
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения в БД"""
        return {
            "token_address": self.token_address,
            "model_name": self.model_name,
            "score_value": self.score_value,
            "score_smoothed": self.score_smoothed,
            "components": self.components.to_dict(),
            "weights": self.weights.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms
        }


class EWMAHelper:
    """
    Помощник для EWMA сглаживания
    """
    
    @staticmethod
    def smooth(current_value: float, previous_value: Optional[float], alpha: float) -> float:
        """
        EWMA сглаживание
        
        Args:
            current_value: Текущее значение
            previous_value: Предыдущее сглаженное значение (None для первого расчета)
            alpha: Параметр сглаживания (0.0 - 1.0)
            
        Returns:
            Сглаженное значение
        """
        if previous_value is None:
            # Первый расчет - возвращаем текущее значение
            return current_value
        
        # EWMA формула: smoothed = alpha * current + (1 - alpha) * previous
        return alpha * current_value + (1 - alpha) * previous_value
    
    @staticmethod
    def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
        """
        Безопасное деление с обработкой нуля
        """
        if denominator == 0 or math.isnan(denominator) or math.isinf(denominator):
            return default
        
        result = numerator / denominator
        
        # Проверяем на NaN и Infinity
        if math.isnan(result) or math.isinf(result):
            return default
            
        return result
    
    @staticmethod
    def safe_log(value: float, default: float = 0.0) -> float:
        """
        Безопасный логарифм с обработкой отрицательных значений
        """
        if value <= 0 or math.isnan(value) or math.isinf(value):
            return default
            
        try:
            result = math.log(value)
            return result if not (math.isnan(result) or math.isinf(result)) else default
        except (ValueError, OverflowError):
            return default


class ScoringModelBase(ABC):
    """
    Базовый класс для всех моделей скоринга
    
    Каждая модель должна наследоваться от этого класса
    и реализовать метод calculate()
    """
    
    def __init__(self, config: ScoringConfig):
        self.config = config
        self.model_name = config.model_name
        
        # Параметры EWMA
        self.ewma_alpha = config.ewma_alpha
        
        # Веса компонентов
        self.weights = ScoringWeights.from_dict(config.weights)
        
        # Проверяем валидность весов
        if not self.weights.validate():
            raise ValueError(f"Invalid weights sum: {sum(self.weights.to_dict().values())}")
    
    @abstractmethod
    async def calculate(
        self, 
        token_address: str,
        metrics_input: TokenMetricsInput,
        previous_result: Optional[ScoringResult] = None
    ) -> ScoringResult:
        """
        Расчет скора для токена
        
        Args:
            token_address: Адрес токена
            metrics_input: Входные метрики
            previous_result: Предыдущий результат для EWMA (None для первого расчета)
            
        Returns:
            Результат скоринга
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Информация о модели
        """
        pass
    
    def _calculate_tx_accel(self, metrics: TokenMetricsInput) -> float:
        """
        Расчет ускорения транзакций
        Формула: (tx_count_5m / 5) / (tx_count_1h / 60)
        """
        tx_rate_5m = metrics.tx_count_5m / 5.0  # транзакций в минуту за последние 5м
        tx_rate_1h = metrics.tx_count_1h / 60.0  # транзакций в минуту за последний час
        
        return EWMAHelper.safe_division(tx_rate_5m, tx_rate_1h, default=0.0)
    
    def _calculate_vol_momentum(self, metrics: TokenMetricsInput) -> float:
        """
        Расчет импульса объема
        Формула: volume_5m / (volume_1h / 12)
        """
        avg_volume_5m_per_hour = float(metrics.volume_1h_usd) / 12.0  # средний 5м объем за час
        
        return EWMAHelper.safe_division(
            float(metrics.volume_5m_usd), 
            avg_volume_5m_per_hour, 
            default=0.0
        )
    
    def _calculate_holder_growth(self, metrics: TokenMetricsInput) -> float:
        """
        Расчет роста держателей
        Формула: log(1 + (holders_now - holders_1h_ago) / holders_1h_ago)
        """
        if metrics.holders_1h_ago is None or metrics.holders_1h_ago <= 0:
            # Если нет исторических данных, возвращаем нейтральное значение
            return 0.0
        
        growth_rate = (metrics.holders_count - metrics.holders_1h_ago) / metrics.holders_1h_ago
        
        # log(1 + growth_rate) для стабилизации
        return EWMAHelper.safe_log(1 + growth_rate, default=0.0)
    
    def _calculate_orderflow_imbalance(self, metrics: TokenMetricsInput) -> float:
        """
        Расчет дисбаланса потока ордеров
        Формула: (buys_volume_5m - sells_volume_5m) / (buys_volume_5m + sells_volume_5m)
        """
        buys = float(metrics.buys_volume_5m_usd)
        sells = float(metrics.sells_volume_5m_usd)
        total_volume = buys + sells
        
        if total_volume <= 0:
            return 0.0
        
        imbalance = (buys - sells) / total_volume
        
        # Ограничиваем диапазон [-1, 1]
        return max(-1.0, min(1.0, imbalance))
    
    def _apply_ewma_smoothing(
        self, 
        components: ScoringComponents,
        previous_components: Optional[ScoringComponents] = None
    ) -> ScoringComponents:
        """
        Применение EWMA сглаживания к компонентам
        """
        if previous_components is None:
            # Первый расчет - берем raw значения
            components.tx_accel_smoothed = components.tx_accel
            components.vol_momentum_smoothed = components.vol_momentum
            components.holder_growth_smoothed = components.holder_growth
            components.orderflow_imbalance_smoothed = components.orderflow_imbalance
        else:
            # Применяем EWMA
            components.tx_accel_smoothed = EWMAHelper.smooth(
                components.tx_accel,
                previous_components.tx_accel_smoothed,
                self.ewma_alpha
            )
            components.vol_momentum_smoothed = EWMAHelper.smooth(
                components.vol_momentum,
                previous_components.vol_momentum_smoothed,
                self.ewma_alpha
            )
            components.holder_growth_smoothed = EWMAHelper.smooth(
                components.holder_growth,
                previous_components.holder_growth_smoothed,
                self.ewma_alpha
            )
            components.orderflow_imbalance_smoothed = EWMAHelper.smooth(
                components.orderflow_imbalance,
                previous_components.orderflow_imbalance_smoothed,
                self.ewma_alpha
            )
        
        return components
    
    def _calculate_final_score(self, components: ScoringComponents) -> float:
        """
        Расчет финального скора по формуле
        Score = W_tx * Tx_Accel + W_vol * Vol_Momentum + W_hld * Holder_Growth + W_oi * Orderflow_Imbalance
        """
        score = (
            self.weights.W_tx * components.tx_accel_smoothed +
            self.weights.W_vol * components.vol_momentum_smoothed +
            self.weights.W_hld * components.holder_growth_smoothed +
            self.weights.W_oi * components.orderflow_imbalance_smoothed
        )
        
        # Ограничиваем диапазон [0, 1] для стабильности
        return max(0.0, min(1.0, score))


class TokenScoringError(Exception):
    """Ошибка расчета скора"""
    pass


class ConfigurationError(Exception):
    """Ошибка конфигурации скоринга"""
    pass
