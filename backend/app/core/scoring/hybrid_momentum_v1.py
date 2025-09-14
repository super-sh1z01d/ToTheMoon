"""
Hybrid Momentum v1 scoring model
Модель скоринга "Гибридный импульс" версия 1

Реализует формулу:
Score = (W_tx * Tx_Accel) + (W_vol * Vol_Momentum) + (W_hld * Holder_Growth) + (W_oi * Orderflow_Imbalance)

Все компоненты сглаживаются через EWMA
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from .base import (
    ScoringModelBase, 
    ScoringResult, 
    ScoringConfig,
    TokenMetricsInput,
    ScoringComponents,
    EWMAHelper,
    TokenScoringError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class HybridMomentumV1(ScoringModelBase):
    """
    Модель скоринга "Гибридный импульс" версия 1
    
    Анализирует:
    - Ускорение транзакций (краткосрочное vs долгосрочное)
    - Импульс объема торгов
    - Рост количества держателей
    - Дисбаланс потока ордеров (покупки vs продажи)
    """
    
    MODEL_NAME = "hybrid_momentum_v1"
    MODEL_VERSION = "1.0.0"
    
    def __init__(self, config: ScoringConfig):
        super().__init__(config)
        
        # Параметры для нормализации значений
        self.normalization_params = {
            "tx_accel_max": 10.0,       # Максимальное ускорение транзакций
            "vol_momentum_max": 5.0,    # Максимальный импульс объема  
            "holder_growth_max": 2.0,   # Максимальный рост держателей (log scale)
            "orderflow_range": 1.0      # Дисбаланс уже в [-1, 1]
        }
        
        logger.info(f"Initialized {self.MODEL_NAME} v{self.MODEL_VERSION}")

    async def calculate(
        self, 
        token_address: str,
        metrics_input: TokenMetricsInput,
        previous_result: Optional[ScoringResult] = None
    ) -> ScoringResult:
        """
        Расчет скора по модели Гибридный импульс
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Calculating score for {token_address[:8]}... using {self.MODEL_NAME}")
            
            # Валидация входных данных
            self._validate_input(metrics_input)
            
            # Расчет компонентов
            components = ScoringComponents()
            
            # 1. Ускорение транзакций
            components.tx_accel = self._calculate_tx_accel(metrics_input)
            
            # 2. Импульс объема
            components.vol_momentum = self._calculate_vol_momentum(metrics_input)
            
            # 3. Рост держателей
            components.holder_growth = self._calculate_holder_growth(metrics_input)
            
            # 4. Дисбаланс потока ордеров
            components.orderflow_imbalance = self._calculate_orderflow_imbalance(metrics_input)
            
            # Нормализация компонентов
            components = self._normalize_components(components)
            
            # EWMA сглаживание
            previous_components = None
            if previous_result:
                previous_components = ScoringComponents(**previous_result.components.to_dict())
            
            components = self._apply_ewma_smoothing(components, previous_components)
            
            # Расчет финального скора
            raw_score = self._calculate_final_score(components)
            
            # EWMA сглаживание финального скора
            previous_score = previous_result.score_smoothed if previous_result else None
            smoothed_score = EWMAHelper.smooth(raw_score, previous_score, self.ewma_alpha)
            
            execution_time = (time.time() - start_time) * 1000  # в миллисекундах
            
            result = ScoringResult(
                token_address=token_address,
                model_name=self.MODEL_NAME,
                score_value=raw_score,
                score_smoothed=smoothed_score,
                components=components,
                weights=self.weights,
                timestamp=datetime.now(),
                execution_time_ms=execution_time
            )
            
            logger.info(
                f"✅ Score calculated for {token_address[:8]}...: {smoothed_score:.3f}",
                extra={
                    "token_address": token_address,
                    "model_name": self.MODEL_NAME,
                    "raw_score": raw_score,
                    "smoothed_score": smoothed_score,
                    "execution_time_ms": execution_time,
                    "tx_accel": components.tx_accel_smoothed,
                    "vol_momentum": components.vol_momentum_smoothed,
                    "holder_growth": components.holder_growth_smoothed,
                    "orderflow_imbalance": components.orderflow_imbalance_smoothed
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"❌ Score calculation failed for {token_address[:8]}...: {e}",
                extra={
                    "token_address": token_address,
                    "model_name": self.MODEL_NAME,
                    "execution_time_ms": execution_time,
                    "error": str(e)
                }
            )
            raise TokenScoringError(f"Score calculation failed: {e}")

    def _validate_input(self, metrics: TokenMetricsInput):
        """
        Валидация входных данных
        """
        if metrics.tx_count_5m < 0 or metrics.tx_count_1h < 0:
            raise TokenScoringError("Transaction counts cannot be negative")
        
        if metrics.volume_5m_usd < 0 or metrics.volume_1h_usd < 0:
            raise TokenScoringError("Volumes cannot be negative")
        
        if metrics.holders_count < 0:
            raise TokenScoringError("Holders count cannot be negative")
        
        if metrics.liquidity_usd < 0:
            raise TokenScoringError("Liquidity cannot be negative")

    def _normalize_components(self, components: ScoringComponents) -> ScoringComponents:
        """
        Нормализация компонентов в диапазон [0, 1]
        """
        # Tx Accel - ограничиваем максимумом
        components.tx_accel = min(
            components.tx_accel / self.normalization_params["tx_accel_max"],
            1.0
        )
        
        # Vol Momentum - ограничиваем максимумом
        components.vol_momentum = min(
            components.vol_momentum / self.normalization_params["vol_momentum_max"],
            1.0
        )
        
        # Holder Growth - уже в log scale, ограничиваем
        components.holder_growth = max(-1.0, min(
            components.holder_growth / self.normalization_params["holder_growth_max"],
            1.0
        ))
        
        # Orderflow Imbalance - уже в [-1, 1], приводим к [0, 1]
        components.orderflow_imbalance = (components.orderflow_imbalance + 1.0) / 2.0
        
        return components

    def get_model_info(self) -> Dict[str, Any]:
        """
        Информация о модели Hybrid Momentum v1
        """
        return {
            "name": self.MODEL_NAME,
            "version": self.MODEL_VERSION,
            "description": "Гибридная модель импульса для краткосрочного арбитража",
            "components": {
                "tx_accel": {
                    "name": "Ускорение транзакций",
                    "formula": "(tx_count_5m / 5) / (tx_count_1h / 60)",
                    "weight": self.weights.W_tx,
                    "description": "Сравнение текущего темпа транзакций со средним"
                },
                "vol_momentum": {
                    "name": "Импульс объема",
                    "formula": "volume_5m / (volume_1h / 12)",
                    "weight": self.weights.W_vol,
                    "description": "Сравнение текущего объема со средним 5м объемом за час"
                },
                "holder_growth": {
                    "name": "Рост держателей",
                    "formula": "log(1 + (holders_now - holders_1h_ago) / holders_1h_ago)",
                    "weight": self.weights.W_hld,
                    "description": "Логарифмический рост количества держателей"
                },
                "orderflow_imbalance": {
                    "name": "Дисбаланс потока ордеров",
                    "formula": "(buys_volume_5m - sells_volume_5m) / (buys_volume_5m + sells_volume_5m)",
                    "weight": self.weights.W_oi,
                    "description": "Преобладание покупок или продаж"
                }
            },
            "ewma_alpha": self.ewma_alpha,
            "weights_sum": sum(self.weights.to_dict().values()),
            "normalization": self.normalization_params,
            "output_range": "[0, 1]",
            "features": [
                "EWMA сглаживание всех компонентов",
                "Автоматическая нормализация",
                "Устойчивость к выбросам",
                "Логарифмическая стабилизация роста держателей"
            ]
        }


class HybridMomentumV1Factory:
    """
    Фабрика для создания экземпляров HybridMomentumV1
    """
    
    @staticmethod
    def create_from_system_config(db_session) -> HybridMomentumV1:
        """
        Создание модели из системной конфигурации
        """
        from app.crud import system_crud
        
        try:
            # Получаем конфигурацию из БД
            model_name = system_crud.get_value(
                db_session, 
                key="SCORING_MODEL", 
                default="hybrid_momentum_v1"
            )
            
            weights_json = system_crud.get_value(
                db_session,
                key="SCORING_WEIGHTS",
                default={"W_tx": 0.25, "W_vol": 0.35, "W_hld": 0.20, "W_oi": 0.20}
            )
            
            ewma_alpha = float(system_crud.get_value(
                db_session,
                key="EWMA_ALPHA",
                default=0.3
            ))
            
            min_threshold = float(system_crud.get_value(
                db_session,
                key="MIN_SCORE_THRESHOLD", 
                default=0.5
            ))
            
            # Создаем конфигурацию
            config = ScoringConfig(
                model_name=model_name,
                weights=weights_json,
                ewma_alpha=ewma_alpha,
                min_score_threshold=min_threshold
            )
            
            logger.info(f"Created {model_name} from system config")
            return HybridMomentumV1(config)
            
        except Exception as e:
            logger.error(f"Failed to create scoring model from config: {e}")
            raise ConfigurationError(f"Failed to load scoring configuration: {e}")
    
    @staticmethod
    def create_default() -> HybridMomentumV1:
        """
        Создание модели с настройками по умолчанию
        """
        config = ScoringConfig(
            model_name="hybrid_momentum_v1",
            weights={
                "W_tx": 0.25,
                "W_vol": 0.35, 
                "W_hld": 0.20,
                "W_oi": 0.20
            },
            ewma_alpha=0.3,
            min_score_threshold=0.5
        )
        
        return HybridMomentumV1(config)
