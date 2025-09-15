"""
Token lifecycle manager
Менеджер жизненного цикла токенов согласно ФЗ
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.models.token import TokenStatus, StatusChangeReason
from app.core.data_sources.birdeye_client import birdeye_manager

logger = logging.getLogger(__name__)


class TokenLifecycleManager:
    """
    Менеджер жизненного цикла токенов
    
    Отвечает за:
    - Мониторинг Initial токенов
    - Активацию при выполнении условий
    - Архивацию по таймауту
    - Деактивацию активных токенов
    """
    
    def __init__(self):
        self.stats = {
            "initial_tokens_checked": 0,
            "active_tokens_checked": 0,
            "tokens_activated": 0,
            "tokens_archived": 0,
            "tokens_deactivated": 0,
            "last_check": None,
            "errors": 0
        }

    async def monitor_initial_tokens(self, db_session) -> Dict[str, Any]:
        """
        Мониторинг токенов в статусе Initial
        
        Проверяет:
        1. Появление пулов с достаточной ликвидностью
        2. Количество транзакций для активации
        3. Таймаут для архивации
        """
        try:
            from app.crud import token_crud, system_crud
            
            logger.info("Monitoring Initial tokens...")
            
            # Получаем Initial токены
            initial_tokens = token_crud.get_by_status(
                db_session,
                status=TokenStatus.INITIAL,
                limit=1000  # Без ограничений для Initial
            )
            
            self.stats["initial_tokens_checked"] = len(initial_tokens)
            
            if not initial_tokens:
                logger.info("No Initial tokens found")
                return {
                    "status": "success",
                    "tokens_processed": 0,
                    "message": "No Initial tokens found"
                }
            
            logger.info(f"Found {len(initial_tokens)} Initial tokens to check")
            
            # Получаем параметры конфигурации
            min_liquidity = float(system_crud.get_value(
                db_session,
                key="MIN_LIQUIDITY_USD",
                default=500
            ))
            
            min_tx_count = int(system_crud.get_value(
                db_session,
                key="MIN_TX_COUNT", 
                default=300
            ))
            
            archival_timeout_hours = int(system_crud.get_value(
                db_session,
                key="ARCHIVAL_TIMEOUT_HOURS",
                default=24
            ))
            
            # Получаем метрики для всех Initial токенов
            await self._fetch_initial_tokens_metrics(initial_tokens, db_session)
            
            activated = 0
            archived = 0
            errors = 0
            
            # Проверяем каждый токен
            for token in initial_tokens:
                try:
                    # Проверка на архивацию по таймауту
                    if self._should_archive_by_timeout(token, archival_timeout_hours):
                        await self._archive_token(
                            token, 
                            StatusChangeReason.ARCHIVAL_TIMEOUT,
                            f"Archived after {archival_timeout_hours}h in Initial status",
                            db_session
                        )
                        archived += 1
                        continue
                    
                    # Проверка на активацию
                    if await self._should_activate_token(token, min_liquidity, min_tx_count, db_session):
                        await self._activate_token(
                            token,
                            StatusChangeReason.ACTIVATION,
                            f"Activated: liquidity≥${min_liquidity}, tx≥{min_tx_count}",
                            db_session
                        )
                        activated += 1
                        
                except Exception as e:
                    logger.error(f"Error processing Initial token {token.token_address}: {e}")
                    errors += 1
            
            self.stats["tokens_activated"] += activated
            self.stats["tokens_archived"] += archived
            self.stats["errors"] += errors
            self.stats["last_check"] = datetime.now()
            
            logger.info(f"Initial tokens monitoring completed: {activated} activated, {archived} archived, {errors} errors")
            
            return {
                "status": "success",
                "tokens_processed": len(initial_tokens),
                "activated": activated,
                "archived": archived,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor Initial tokens: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "error": str(e)
            }

    async def monitor_active_tokens_lifecycle(self, db_session) -> Dict[str, Any]:
        """
        Мониторинг жизненного цикла активных токенов
        
        Проверяет:
        1. Низкий скор длительное время -> возврат в Initial
        2. Низкая активность в пулах -> возврат в Initial
        """
        try:
            from app.crud import token_crud, system_crud
            
            logger.info("Monitoring Active tokens lifecycle...")
            
            # Получаем Active токены
            active_tokens = token_crud.get_by_status(
                db_session,
                status=TokenStatus.ACTIVE,
                limit=1000
            )
            
            self.stats["active_tokens_checked"] = len(active_tokens)
            
            if not active_tokens:
                return {
                    "status": "success",
                    "tokens_processed": 0,
                    "message": "No Active tokens found"
                }
            
            logger.info(f"Found {len(active_tokens)} Active tokens to check")
            
            # Получаем параметры конфигурации
            min_score_threshold = float(system_crud.get_value(
                db_session,
                key="MIN_SCORE_THRESHOLD",
                default=0.5
            ))
            
            low_score_hours = int(system_crud.get_value(
                db_session,
                key="LOW_SCORE_HOURS",
                default=6
            ))
            
            min_tx_count = int(system_crud.get_value(
                db_session,
                key="MIN_TX_COUNT",
                default=300
            ))
            
            low_activity_checks = int(system_crud.get_value(
                db_session,
                key="LOW_ACTIVITY_CHECKS",
                default=10
            ))
            
            deactivated = 0
            errors = 0
            
            # Проверяем каждый активный токен
            for token in active_tokens:
                try:
                    # Проверка на низкий скор
                    if await self._should_deactivate_by_score(
                        token, min_score_threshold, low_score_hours, db_session
                    ):
                        await self._deactivate_token(
                            token,
                            StatusChangeReason.LOW_SCORE,
                            f"Deactivated: score<{min_score_threshold} for {low_score_hours}h",
                            db_session
                        )
                        deactivated += 1
                        continue
                    
                    # Проверка на низкую активность
                    if await self._should_deactivate_by_activity(
                        token, min_tx_count, low_activity_checks, db_session
                    ):
                        await self._deactivate_token(
                            token,
                            StatusChangeReason.LOW_ACTIVITY,
                            f"Deactivated: tx<{min_tx_count} for {low_activity_checks} checks",
                            db_session
                        )
                        deactivated += 1
                        
                except Exception as e:
                    logger.error(f"Error processing Active token {token.token_address}: {e}")
                    errors += 1
            
            self.stats["tokens_deactivated"] += deactivated
            self.stats["errors"] += errors
            self.stats["last_check"] = datetime.now()
            
            logger.info(f"Active tokens lifecycle completed: {deactivated} deactivated, {errors} errors")
            
            return {
                "status": "success",
                "tokens_processed": len(active_tokens),
                "deactivated": deactivated,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor Active tokens lifecycle: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "error": str(e)
            }

    async def _fetch_initial_tokens_metrics(self, tokens: List, db_session):
        """
        Получение метрик для Initial токенов
        """
        try:
            # Инициализируем Birdeye менеджер если нужно
            if not birdeye_manager.client:
                await birdeye_manager.initialize()
            
            successful = 0
            failed = 0
            
            for token in tokens:
                try:
                    # Получаем метрики с задержкой для rate limits
                    success = await birdeye_manager.save_token_metrics(token.token_address)
                    
                    if success:
                        successful += 1
                    else:
                        failed += 1
                        
                    # Задержка между запросами (больше чем для Active)
                    import asyncio
                    await asyncio.sleep(1.0)  # 1 секунда для Initial токенов
                    
                except Exception as e:
                    logger.error(f"Error fetching metrics for Initial token {token.token_address}: {e}")
                    failed += 1
            
            logger.info(f"Initial tokens metrics: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Failed to fetch Initial tokens metrics: {e}")

    def _should_archive_by_timeout(self, token, timeout_hours: int) -> bool:
        """
        Проверка архивации по таймауту
        """
        if token.status != TokenStatus.INITIAL:
            return False
        
        # Проверяем время в статусе Initial
        time_in_initial = datetime.now() - token.created_at.replace(tzinfo=None)
        
        return time_in_initial.total_seconds() > (timeout_hours * 3600)

    async def _should_activate_token(
        self, 
        token, 
        min_liquidity: float, 
        min_tx_count: int,
        db_session
    ) -> bool:
        """
        Проверка условий активации токена
        
        Условия:
        1. Есть пул с ликвидностью ≥ min_liquidity
        2. Количество транзакций ≥ min_tx_count
        """
        try:
            from app.crud import token_metrics_crud, pool_crud
            
            # Проверяем наличие пулов
            pools = pool_crud.get_by_token(db_session, token_id=token.id)
            if not pools:
                return False
            
            # Получаем последние метрики
            latest_metrics = token_metrics_crud.get_latest(db_session, token_id=token.id)
            if not latest_metrics:
                return False
            
            # Проверяем ликвидность
            if float(latest_metrics.liquidity_usd) < min_liquidity:
                return False
            
            # Проверяем количество транзакций
            if latest_metrics.tx_count_1h < min_tx_count:
                return False
            
            logger.info(
                f"Token {token.token_address[:8]}... meets activation criteria: "
                f"liquidity=${latest_metrics.liquidity_usd}, tx={latest_metrics.tx_count_1h}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking activation conditions for {token.token_address}: {e}")
            return False

    async def _should_deactivate_by_score(
        self, 
        token, 
        min_score: float, 
        low_score_hours: int,
        db_session
    ) -> bool:
        """
        Проверка деактивации по низкому скору
        """
        try:
            from app.crud import token_scores_crud
            
            # Получаем скоры за период
            cutoff_time = datetime.now() - timedelta(hours=low_score_hours)
            
            scores = token_scores_crud.get_by_token(
                db_session,
                token_id=token.id,
                hours_back=low_score_hours,
                limit=1000
            )
            
            if not scores:
                return False
            
            # Проверяем что все скоры ниже порога
            low_scores = [s for s in scores if s.score_value < min_score]
            
            # Если все скоры за период ниже порога
            if len(low_scores) == len(scores) and len(scores) >= 5:  # Минимум 5 измерений
                logger.info(
                    f"Token {token.token_address[:8]}... has low score for {low_score_hours}h: "
                    f"avg={sum(s.score_value for s in scores)/len(scores):.3f} < {min_score}"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking score deactivation for {token.token_address}: {e}")
            return False

    async def _should_deactivate_by_activity(
        self, 
        token, 
        min_tx_count: int, 
        low_activity_checks: int,
        db_session
    ) -> bool:
        """
        Проверка деактивации по низкой активности
        """
        try:
            from app.crud import token_metrics_crud
            
            # Получаем последние метрики для проверки активности
            recent_metrics = token_metrics_crud.get_by_token(
                db_session,
                token_id=token.id,
                hours_back=low_activity_checks,  # Используем как количество часов
                limit=low_activity_checks
            )
            
            if len(recent_metrics) < low_activity_checks:
                return False  # Недостаточно данных
            
            # Проверяем что активность низкая
            low_activity_count = 0
            for metrics in recent_metrics:
                if metrics.tx_count_1h < min_tx_count:
                    low_activity_count += 1
            
            # Если большинство проверок показывают низкую активность
            if low_activity_count >= (low_activity_checks * 0.8):  # 80% проверок
                logger.info(
                    f"Token {token.token_address[:8]}... has low activity: "
                    f"{low_activity_count}/{low_activity_checks} checks below {min_tx_count} tx"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking activity deactivation for {token.token_address}: {e}")
            return False

    async def _activate_token(
        self, 
        token, 
        reason: StatusChangeReason,
        metadata: str,
        db_session
    ):
        """
        Активация токена
        """
        try:
            from app.crud import token_crud
            
            updated_token = token_crud.update_status(
                db_session,
                token=token,
                new_status=TokenStatus.ACTIVE,
                reason=reason,
                metadata=metadata
            )
            
            logger.info(
                f"✅ Token activated: {token.token_address[:8]}...",
                extra={
                    "token_id": str(token.id),
                    "token_address": token.token_address,
                    "old_status": "initial",
                    "new_status": "active",
                    "reason": reason.value,
                    "metadata": metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to activate token {token.token_address}: {e}")
            raise

    async def _archive_token(
        self, 
        token, 
        reason: StatusChangeReason,
        metadata: str,
        db_session
    ):
        """
        Архивация токена
        """
        try:
            from app.crud import token_crud
            
            updated_token = token_crud.update_status(
                db_session,
                token=token,
                new_status=TokenStatus.ARCHIVED,
                reason=reason,
                metadata=metadata
            )
            
            logger.info(
                f"📦 Token archived: {token.token_address[:8]}...",
                extra={
                    "token_id": str(token.id),
                    "token_address": token.token_address,
                    "old_status": token.status.value,
                    "new_status": "archived",
                    "reason": reason.value,
                    "metadata": metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to archive token {token.token_address}: {e}")
            raise

    async def _deactivate_token(
        self, 
        token, 
        reason: StatusChangeReason,
        metadata: str,
        db_session
    ):
        """
        Деактивация токена (возврат в Initial)
        """
        try:
            from app.crud import token_crud
            
            updated_token = token_crud.update_status(
                db_session,
                token=token,
                new_status=TokenStatus.INITIAL,
                reason=reason,
                metadata=metadata
            )
            
            logger.info(
                f"⬇️ Token deactivated: {token.token_address[:8]}...",
                extra={
                    "token_id": str(token.id),
                    "token_address": token.token_address,
                    "old_status": "active",
                    "new_status": "initial",
                    "reason": reason.value,
                    "metadata": metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to deactivate token {token.token_address}: {e}")
            raise

    async def get_lifecycle_stats(self, db_session) -> Dict[str, Any]:
        """
        Получение статистики жизненного цикла
        """
        try:
            from app.crud import token_crud
            from app.models.token import TokenStatusHistory
            from sqlalchemy import func, desc
            
            # Базовая статистика токенов
            stats = token_crud.get_stats(db_session)
            
            # Статистика переходов за последние 24 часа
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            transitions_24h = db_session.query(
                TokenStatusHistory.reason,
                func.count(TokenStatusHistory.id).label('count')
            ).filter(
                TokenStatusHistory.changed_at >= cutoff_time
            ).group_by(TokenStatusHistory.reason).all()
            
            transitions_data = {}
            for transition in transitions_24h:
                transitions_data[transition.reason.value] = transition.count
            
            # Последние переходы
            recent_transitions = db_session.query(TokenStatusHistory).order_by(
                desc(TokenStatusHistory.changed_at)
            ).limit(10).all()
            
            recent_data = []
            for transition in recent_transitions:
                token = token_crud.get(db_session, id=transition.token_id)
                recent_data.append({
                    "token_address": token.token_address if token else "unknown",
                    "old_status": transition.old_status.value if transition.old_status else None,
                    "new_status": transition.new_status.value,
                    "reason": transition.reason.value,
                    "changed_at": transition.changed_at.isoformat(),
                    "metadata": transition.change_metadata
                })
            
            result = {
                "token_stats": stats,
                "lifecycle_stats": self.stats,
                "transitions_24h": transitions_data,
                "recent_transitions": recent_data,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get lifecycle stats: {e}")
            return {
                "error": str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики менеджера
        """
        return self.stats.copy()


# Глобальный экземпляр менеджера
lifecycle_manager = TokenLifecycleManager()
