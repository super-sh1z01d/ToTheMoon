"""
TOML configuration generator for arbitrage bot
Генератор TOML конфигурации для арбитражного бота NotArb
"""

import logging
import toml
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class TOMLConfigGenerator:
    """
    Генератор TOML конфигурации для арбитражного бота
    
    Логика согласно ФЗ:
    1. Отбирает токены в статусе Active
    2. Фильтрует по min_score_for_config
    3. Сортирует по Score по убыванию
    4. Выбирает топ-3 токена
    5. Включает их активные пулы
    """
    
    def __init__(self):
        self.stats = {
            "toml_generated": 0,
            "last_generation": None,
            "tokens_exported": 0,
            "pools_exported": 0,
            "errors": 0
        }

    async def generate_dynamic_strategy_toml(self, db_session) -> str:
        """
        Генерация TOML конфигурации для динамической стратегии
        
        Returns:
            TOML строка готовая для отдачи боту
        """
        try:
            logger.info("Generating dynamic strategy TOML...")
            
            # Получаем параметры конфигурации
            config_params = await self._load_export_config(db_session)
            
            # Получаем топ токены
            top_tokens = await self._get_top_tokens_for_export(db_session, config_params)
            
            if not top_tokens:
                # Генерируем пустую конфигурацию
                logger.warning("No tokens meet export criteria")
                return self._generate_empty_toml(config_params)
            
            # Генерируем TOML
            toml_config = await self._build_toml_config(top_tokens, config_params, db_session)
            
            # Конвертируем в TOML строку
            toml_string = toml.dumps(toml_config)
            
            self.stats["toml_generated"] += 1
            self.stats["last_generation"] = datetime.now()
            self.stats["tokens_exported"] = len(top_tokens)
            
            logger.info(
                f"✅ TOML generated with {len(top_tokens)} tokens",
                extra={
                    "tokens_count": len(top_tokens),
                    "config_size_bytes": len(toml_string),
                    "min_score": config_params["min_score_for_config"],
                    "operation": "toml_generation"
                }
            )
            
            return toml_string
            
        except Exception as e:
            logger.error(f"Failed to generate TOML: {e}")
            self.stats["errors"] += 1
            raise

    async def _load_export_config(self, db_session) -> Dict[str, Any]:
        """
        Загрузка параметров экспорта из конфигурации
        """
        from app.crud import system_crud
        
        return {
            "min_score_for_config": float(system_crud.get_value(
                db_session,
                key="MIN_SCORE_FOR_CONFIG",
                default=0.7
            )),
            "config_top_count": int(system_crud.get_value(
                db_session,
                key="CONFIG_TOP_COUNT",
                default=3
            )),
            "scoring_model": system_crud.get_value(
                db_session,
                key="SCORING_MODEL",
                default="hybrid_momentum_v1"
            )
        }

    async def _get_top_tokens_for_export(
        self, 
        db_session, 
        config_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Получение топ токенов для экспорта согласно логике ФЗ
        
        1. Токены в статусе Active
        2. Score >= min_score_for_config  
        3. Сортировка по Score убыванию
        4. Топ-3 токена
        """
        try:
            from app.crud.metrics import token_scores_crud
            
            min_score = config_params["min_score_for_config"]
            top_count = config_params["config_top_count"]
            model_name = config_params["scoring_model"]
            
            # Получаем топ токены из scoring API
            top_tokens = token_scores_crud.get_top_tokens(
                db_session,
                model_name=model_name,
                min_score=min_score,
                limit=top_count,
                hours_back=2  # Последние 2 часа для актуальности
            )
            
            logger.info(f"Found {len(top_tokens)} tokens for export (min_score={min_score})")
            
            return top_tokens
            
        except Exception as e:
            logger.error(f"Failed to get top tokens for export: {e}")
            return []

    async def _build_toml_config(
        self, 
        top_tokens: List[Dict[str, Any]], 
        config_params: Dict[str, Any],
        db_session
    ) -> Dict[str, Any]:
        """
        Построение TOML конфигурации
        """
        try:
            from app.crud import token_crud, pool_crud
            from uuid import UUID
            
            # Заголовок конфигурации
            toml_config = {
                "strategy": {
                    "name": "dynamic_strategy",
                    "description": "ToTheMoon2 dynamic arbitrage strategy",
                    "version": "1.0.0",
                    "generated_at": datetime.now().isoformat(),
                    "model_name": config_params["scoring_model"],
                    "min_score_threshold": config_params["min_score_for_config"],
                    "tokens_count": len(top_tokens)
                },
                "tokens": []
            }
            
            pools_exported = 0
            
            # Добавляем каждый токен с его пулами
            for token_data in top_tokens:
                try:
                    # Получаем токен из БД
                    token = token_crud.get(db_session, id=UUID(token_data["token_id"]))
                    if not token:
                        logger.warning(f"Token {token_data['token_id']} not found")
                        continue
                    
                    # Получаем активные пулы
                    active_pools = pool_crud.get_by_token(
                        db_session,
                        token_id=token.id,
                        active_only=True
                    )
                    
                    if not active_pools:
                        logger.warning(f"No active pools for token {token.token_address[:8]}...")
                        continue
                    
                    # Группируем пулы по DEX
                    pools_by_dex = {}
                    for pool in active_pools:
                        dex = pool.dex_name
                        if dex not in pools_by_dex:
                            pools_by_dex[dex] = []
                        pools_by_dex[dex].append(pool.pool_address)
                    
                    # Добавляем токен в конфигурацию
                    token_config = {
                        "address": token.token_address,
                        "score": float(token_data["score_value"]),
                        "calculated_at": token_data["calculated_at"],
                        "status": token.status.value,
                        "pools_count": len(active_pools),
                        "pools": pools_by_dex,
                        "metadata": {
                            "token_id": str(token.id),
                            "last_score_calculated": token.last_score_calculated_at.isoformat() if token.last_score_calculated_at else None,
                            "activated_at": token.activated_at.isoformat() if token.activated_at else None
                        }
                    }
                    
                    toml_config["tokens"].append(token_config)
                    pools_exported += len(active_pools)
                    
                    logger.debug(f"Added token {token.token_address[:8]}... with {len(active_pools)} pools")
                    
                except Exception as e:
                    logger.error(f"Error processing token {token_data.get('token_id', 'unknown')}: {e}")
                    continue
            
            self.stats["pools_exported"] = pools_exported
            
            # Добавляем метаданные
            toml_config["metadata"] = {
                "source": "ToTheMoon2",
                "generation_time": datetime.now().isoformat(),
                "tokens_selected": len(toml_config["tokens"]),
                "total_pools": pools_exported,
                "selection_criteria": {
                    "status": "active",
                    "min_score": config_params["min_score_for_config"],
                    "top_count": config_params["config_top_count"],
                    "model": config_params["scoring_model"]
                }
            }
            
            return toml_config
            
        except Exception as e:
            logger.error(f"Failed to build TOML config: {e}")
            raise

    def _generate_empty_toml(self, config_params: Dict[str, Any]) -> str:
        """
        Генерация пустой TOML конфигурации когда нет подходящих токенов
        """
        empty_config = {
            "strategy": {
                "name": "dynamic_strategy",
                "description": "ToTheMoon2 dynamic arbitrage strategy",
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "model_name": config_params["scoring_model"],
                "min_score_threshold": config_params["min_score_for_config"],
                "tokens_count": 0,
                "warning": "No tokens meet the export criteria"
            },
            "tokens": [],
            "metadata": {
                "source": "ToTheMoon2",
                "generation_time": datetime.now().isoformat(),
                "tokens_selected": 0,
                "total_pools": 0,
                "selection_criteria": {
                    "status": "active",
                    "min_score": config_params["min_score_for_config"],
                    "top_count": config_params["config_top_count"],
                    "model": config_params["scoring_model"]
                }
            }
        }
        
        return toml.dumps(empty_config)

    async def generate_custom_toml(
        self, 
        db_session,
        min_score: Optional[float] = None,
        top_count: Optional[int] = None,
        model_name: Optional[str] = None
    ) -> str:
        """
        Генерация кастомной TOML конфигурации с переопределенными параметрами
        """
        try:
            # Загружаем базовую конфигурацию
            config_params = await self._load_export_config(db_session)
            
            # Переопределяем параметры если заданы
            if min_score is not None:
                config_params["min_score_for_config"] = min_score
            if top_count is not None:
                config_params["config_top_count"] = top_count
            if model_name is not None:
                config_params["scoring_model"] = model_name
            
            # Генерируем TOML
            return await self.generate_dynamic_strategy_toml(db_session)
            
        except Exception as e:
            logger.error(f"Failed to generate custom TOML: {e}")
            raise

    async def get_export_preview(self, db_session) -> Dict[str, Any]:
        """
        Получение предварительного просмотра экспорта без генерации TOML
        """
        try:
            # Получаем параметры
            config_params = await self._load_export_config(db_session)
            
            # Получаем токены
            top_tokens = await self._get_top_tokens_for_export(db_session, config_params)
            
            # Формируем превью
            preview = {
                "export_config": config_params,
                "selected_tokens": [],
                "total_tokens": len(top_tokens),
                "total_pools": 0
            }
            
            # Добавляем информацию о токенах
            from app.crud import token_crud, pool_crud
            from uuid import UUID
            
            for token_data in top_tokens:
                token = token_crud.get(db_session, id=UUID(token_data["token_id"]))
                if token:
                    active_pools = pool_crud.get_by_token(
                        db_session,
                        token_id=token.id,
                        active_only=True
                    )
                    
                    preview["selected_tokens"].append({
                        "token_address": token.token_address,
                        "score": token_data["score_value"],
                        "pools_count": len(active_pools),
                        "dex_names": list(set(p.dex_name for p in active_pools))
                    })
                    
                    preview["total_pools"] += len(active_pools)
            
            return preview
            
        except Exception as e:
            logger.error(f"Failed to get export preview: {e}")
            return {
                "error": str(e),
                "export_config": {},
                "selected_tokens": [],
                "total_tokens": 0,
                "total_pools": 0
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики генератора
        """
        return self.stats.copy()

    async def validate_export_config(self, db_session) -> Dict[str, Any]:
        """
        Валидация конфигурации экспорта
        """
        try:
            from app.crud import system_crud, token_crud
            from app.models.token import TokenStatus
            
            # Проверяем параметры
            config_params = await self._load_export_config(db_session)
            
            # Статистика токенов
            active_tokens_count = token_crud.count_by_status(
                db_session, 
                status=TokenStatus.ACTIVE
            )
            
            # Проверяем что параметры валидны
            validation_result = {
                "valid": True,
                "issues": [],
                "config": config_params,
                "active_tokens_count": active_tokens_count,
                "estimated_export_count": 0
            }
            
            # Валидация min_score_for_config
            min_score = config_params["min_score_for_config"]
            if not (0.0 <= min_score <= 1.0):
                validation_result["valid"] = False
                validation_result["issues"].append(
                    f"min_score_for_config должен быть между 0.0 и 1.0, получен {min_score}"
                )
            
            # Валидация config_top_count
            top_count = config_params["config_top_count"]
            if top_count <= 0:
                validation_result["valid"] = False
                validation_result["issues"].append(
                    f"config_top_count должен быть положительным, получен {top_count}"
                )
            
            # Проверяем что есть активные токены
            if active_tokens_count == 0:
                validation_result["issues"].append("Нет активных токенов для экспорта")
            
            # Оценочное количество токенов для экспорта
            top_tokens = await self._get_top_tokens_for_export(db_session, config_params)
            validation_result["estimated_export_count"] = len(top_tokens)
            
            if len(top_tokens) == 0:
                validation_result["issues"].append(
                    f"Нет токенов со скором >= {min_score} для экспорта"
                )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate export config: {e}")
            return {
                "valid": False,
                "issues": [f"Ошибка валидации: {e}"],
                "config": {},
                "active_tokens_count": 0,
                "estimated_export_count": 0
            }


# Глобальный экземпляр генератора
toml_generator = TOMLConfigGenerator()
