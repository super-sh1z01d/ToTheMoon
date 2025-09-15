"""
Scoring manager for coordinating score calculations
Менеджер скоринга для координации расчетов
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID

# AVAILABLE_MODELS будет импортирован локально чтобы избежать циклических импортов
from app.core.scoring.base import (
    ScoringModelBase, 
    ScoringResult, 
    ScoringConfig,
    TokenMetricsInput,
    ScoringComponents,
    TokenScoringError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class ScoringManager:
    """
    Менеджер для управления скорингом токенов
    
    Отвечает за:
    - Загрузку конфигурации скоринга
    - Создание экземпляров моделей
    - Получение метрик для расчета
    - Сохранение результатов
    - Обновление токенов
    """
    
    def __init__(self):
        self.current_model: Optional[ScoringModelBase] = None
        self.model_name: Optional[str] = None
        
        # Статистика
        self.stats = {
            "scores_calculated": 0,
            "errors": 0,
            "last_calculation": None,
            "model_loaded": None
        }

    async def initialize_from_config(self, db_session):
        """
        Инициализация менеджера из системной конфигурации
        """
        try:
            from app.crud import system_crud
            
            # Получаем название активной модели
            model_name = system_crud.get_value(
                db_session,
                key="SCORING_MODEL",
                default="hybrid_momentum_v1"
            )
            
            # Импортируем локально чтобы избежать циклических импортов
            from app.core.scoring.hybrid_momentum_v1 import HybridMomentumV1
            
            # Локальный словарь доступных моделей
            available_models = {
                "hybrid_momentum_v1": HybridMomentumV1,
            }
            
            if model_name not in available_models:
                raise ConfigurationError(f"Unknown scoring model: {model_name}")
            
            # Создаем модель
            model_class = available_models[model_name]
            
            # Загружаем конфигурацию
            config = await self._load_config_from_db(db_session, model_name)
            
            # Создаем экземпляр модели
            self.current_model = model_class(config)
            self.model_name = model_name
            self.stats["model_loaded"] = datetime.now()
            
            logger.info(f"✅ Scoring manager initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize scoring manager: {e}")
            raise

    async def _load_config_from_db(self, db_session, model_name: str) -> ScoringConfig:
        """
        Загрузка конфигурации из БД
        """
        from app.crud import system_crud
        
        try:
            weights = system_crud.get_value(
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
            
            return ScoringConfig(
                model_name=model_name,
                weights=weights,
                ewma_alpha=ewma_alpha,
                min_score_threshold=min_threshold
            )
            
        except Exception as e:
            logger.error(f"Failed to load scoring config: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")

    async def calculate_score_for_token(
        self, 
        token_address: str,
        db_session
    ) -> Optional[ScoringResult]:
        """
        Расчет скора для конкретного токена
        """
        try:
            if not self.current_model:
                await self.initialize_from_config(db_session)
            
            # Получаем метрики токена
            metrics_input = await self._get_token_metrics(token_address, db_session)
            if not metrics_input:
                logger.warning(f"No metrics available for token {token_address[:8]}...")
                return None
            
            # Получаем предыдущий результат для EWMA
            previous_result = await self._get_previous_score(token_address, db_session)
            
            # Рассчитываем скор
            result = await self.current_model.calculate(
                token_address,
                metrics_input,
                previous_result
            )
            
            # Сохраняем результат
            await self._save_score_result(result, db_session)
            
            # Обновляем токен
            await self._update_token_score(token_address, result, db_session)
            
            self.stats["scores_calculated"] += 1
            self.stats["last_calculation"] = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate score for {token_address}: {e}")
            self.stats["errors"] += 1
            return None

    async def _get_token_metrics(
        self, 
        token_address: str, 
        db_session
    ) -> Optional[TokenMetricsInput]:
        """
        Получение последних метрик токена для расчета
        """
        try:
            from app.crud import token_crud, token_metrics_crud
            
            # Находим токен
            token = token_crud.get_by_address(db_session, token_address=token_address)
            if not token:
                logger.warning(f"Token {token_address} not found in database")
                return None
            
            # Получаем последние метрики
            latest_metrics = token_metrics_crud.get_latest(db_session, token_id=token.id)
            if not latest_metrics:
                logger.warning(f"No metrics found for token {token_address}")
                return None
            
            # Получаем метрики час назад для роста держателей
            metrics_1h_ago = token_metrics_crud.get_by_token(
                db_session,
                token_id=token.id,
                hours_back=1,
                limit=1
            )
            
            holders_1h_ago = None
            if metrics_1h_ago:
                holders_1h_ago = metrics_1h_ago[0].holders_count
            
            # Создаем входные данные
            return TokenMetricsInput(
                tx_count_5m=latest_metrics.tx_count_5m,
                tx_count_1h=latest_metrics.tx_count_1h,
                volume_5m_usd=latest_metrics.volume_5m_usd,
                volume_1h_usd=latest_metrics.volume_1h_usd,
                buys_volume_5m_usd=latest_metrics.buys_volume_5m_usd,
                sells_volume_5m_usd=latest_metrics.sells_volume_5m_usd,
                holders_count=latest_metrics.holders_count,
                holders_1h_ago=holders_1h_ago,
                liquidity_usd=latest_metrics.liquidity_usd,
                timestamp=latest_metrics.timestamp
            )
            
        except Exception as e:
            logger.error(f"Failed to get token metrics for {token_address}: {e}")
            return None

    async def _get_previous_score(
        self, 
        token_address: str, 
        db_session
    ) -> Optional[ScoringResult]:
        """
        Получение предыдущего результата скоринга для EWMA
        """
        try:
            from app.crud import token_crud, token_scores_crud
            
            # Находим токен
            token = token_crud.get_by_address(db_session, token_address=token_address)
            if not token:
                return None
            
            # Получаем последний скор
            latest_score = token_scores_crud.get_latest_score(
                db_session,
                token_id=token.id,
                model_name=self.model_name
            )
            
            if not latest_score:
                return None
            
            # Восстанавливаем ScoringResult
            components_data = latest_score.components or {}
            components = ScoringComponents(**components_data)
            
            # Получаем веса из компонентов (или используем текущие)
            weights_data = components_data.get("weights", self.current_model.weights.to_dict())
            from app.core.scoring.base import ScoringWeights
            weights = ScoringWeights.from_dict(weights_data)
            
            return ScoringResult(
                token_address=token_address,
                model_name=latest_score.model_name,
                score_value=latest_score.score_value,
                score_smoothed=latest_score.score_value,  # Используем как smoothed
                components=components,
                weights=weights,
                timestamp=latest_score.calculated_at,
                execution_time_ms=0.0
            )
            
        except Exception as e:
            logger.error(f"Failed to get previous score for {token_address}: {e}")
            return None

    async def _save_score_result(self, result: ScoringResult, db_session):
        """
        Сохранение результата скоринга в БД
        """
        try:
            from app.models.metrics import TokenScores
            from app.crud import token_crud
            
            # Находим токен
            token = token_crud.get_by_address(db_session, token_address=result.token_address)
            if not token:
                logger.error(f"Token {result.token_address} not found for score saving")
                return
            
            # Создаем запись скора
            token_score = TokenScores(
                token_id=token.id,
                model_name=result.model_name,
                score_value=result.score_smoothed,  # Сохраняем сглаженный скор
                calculated_at=result.timestamp,
                components=result.to_dict()  # Сохраняем все детали расчета
            )
            
            db_session.add(token_score)
            db_session.commit()
            
            logger.debug(f"Score saved for {result.token_address[:8]}...")
            
        except Exception as e:
            logger.error(f"Failed to save score result: {e}")
            db_session.rollback()
            raise

    async def _update_token_score(
        self, 
        token_address: str, 
        result: ScoringResult, 
        db_session
    ):
        """
        Обновление токена с новым скором
        """
        try:
            from app.crud import token_crud
            
            # Находим токен
            token = token_crud.get_by_address(db_session, token_address=token_address)
            if not token:
                return
            
            # Обновляем поля скора
            update_data = {
                "last_score_value": result.score_smoothed,
                "last_score_calculated_at": result.timestamp
            }
            
            token_crud.update(db_session, db_obj=token, obj_in=update_data)
            
            logger.debug(f"Token score updated for {token_address[:8]}...")
            
        except Exception as e:
            logger.error(f"Failed to update token score: {e}")
            raise

    async def calculate_scores_for_active_tokens(self, db_session) -> Dict[str, Any]:
        """
        Расчет скоров для всех активных токенов
        """
        try:
            from app.crud import token_crud
            from app.models.token import TokenStatus
            
            # Получаем активные токены
            active_tokens = token_crud.get_by_status(
                db_session,
                status=TokenStatus.ACTIVE,
                limit=1000  # Ограничение для производительности
            )
            
            logger.info(f"Calculating scores for {len(active_tokens)} active tokens")
            
            if not active_tokens:
                return {
                    "status": "success",
                    "tokens_processed": 0,
                    "message": "No active tokens found"
                }
            
            # Инициализируем модель если нужно
            if not self.current_model:
                await self.initialize_from_config(db_session)
            
            successful = 0
            failed = 0
            results = []
            
            for token in active_tokens:
                try:
                    result = await self.calculate_score_for_token(
                        token.token_address,
                        db_session
                    )
                    
                    if result:
                        successful += 1
                        results.append({
                            "token_address": token.token_address,
                            "score": result.score_smoothed,
                            "timestamp": result.timestamp.isoformat()
                        })
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error calculating score for {token.token_address}: {e}")
                    failed += 1
            
            logger.info(f"Scoring completed: {successful} successful, {failed} failed")
            
            return {
                "status": "success",
                "tokens_processed": len(active_tokens),
                "successful": successful,
                "failed": failed,
                "model_name": self.model_name,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate scores for active tokens: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Получение информации о текущей модели
        """
        if not self.current_model:
            return {
                "model_loaded": False,
                "error": "No model loaded"
            }
        
        info = self.current_model.get_model_info()
        info.update({
            "model_loaded": True,
            "loaded_at": self.stats["model_loaded"].isoformat() if self.stats["model_loaded"] else None
        })
        
        return info

    async def reload_model(self, db_session) -> bool:
        """
        Перезагрузка модели из конфигурации
        """
        try:
            logger.info("Reloading scoring model from configuration...")
            
            old_model = self.model_name
            await self.initialize_from_config(db_session)
            
            logger.info(f"Model reloaded: {old_model} -> {self.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload scoring model: {e}")
            return False

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Получение списка доступных моделей
        """
        models = []
        
        # Локальный список моделей чтобы избежать циклических импортов
        from app.core.scoring.hybrid_momentum_v1 import HybridMomentumV1
        
        available_models = {
            "hybrid_momentum_v1": HybridMomentumV1,
        }
        
        for model_name, model_class in available_models.items():
            try:
                # Создаем временный экземпляр для получения информации
                from app.core.scoring.hybrid_momentum_v1 import HybridMomentumV1Factory
                
                if model_name == "hybrid_momentum_v1":
                    temp_model = HybridMomentumV1Factory.create_default()
                    info = temp_model.get_model_info()
                    info["available"] = True
                else:
                    info = {
                        "name": model_name,
                        "available": False,
                        "description": "Model not implemented yet"
                    }
                
                models.append(info)
                
            except Exception as e:
                logger.error(f"Error getting info for model {model_name}: {e}")
                models.append({
                    "name": model_name,
                    "available": False,
                    "error": str(e)
                })
        
        return models

    async def test_model_calculation(
        self, 
        test_token_address: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Тестовый расчет скора для проверки модели
        """
        try:
            if not self.current_model:
                await self.initialize_from_config(db_session)
            
            logger.info(f"Testing score calculation for {test_token_address[:8]}...")
            
            result = await self.calculate_score_for_token(test_token_address, db_session)
            
            if result:
                return {
                    "status": "success",
                    "model_name": result.model_name,
                    "token_address": result.token_address,
                    "score_value": result.score_value,
                    "score_smoothed": result.score_smoothed,
                    "components": result.components.to_dict(),
                    "execution_time_ms": result.execution_time_ms,
                    "timestamp": result.timestamp.isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "error": "No result returned"
                }
                
        except Exception as e:
            logger.error(f"Test calculation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики работы
        """
        stats = self.stats.copy()
        
        if self.current_model:
            stats.update({
                "model_name": self.model_name,
                "model_info": self.current_model.get_model_info()
            })
        
        return stats


# Глобальный экземпляр менеджера
scoring_manager = ScoringManager()
