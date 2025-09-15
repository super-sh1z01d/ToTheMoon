"""
Celery tasks for token lifecycle management
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from celery import Celery
from app.core.lifecycle.manager import lifecycle_manager

logger = logging.getLogger(__name__)

# Создаем Celery app (будет переопределен в main celery config)
celery_app = Celery("lifecycle_tasks")


@celery_app.task(bind=True, name="monitor_initial_tokens")
def monitor_initial_tokens_task(self) -> Dict[str, Any]:
    """
    Celery task для мониторинга токенов в статусе Initial
    
    Проверяет:
    - Условия активации (ликвидность + транзакции)
    - Таймаут для архивации (24 часа)
    
    Выполняется каждые 10 минут
    """
    try:
        logger.info("Starting Initial tokens monitoring...")
        
        from app.database import SessionLocal
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        db = SessionLocal()
        
        try:
            # Запускаем asyncio loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    lifecycle_manager.monitor_initial_tokens(db)
                )
                
                logger.info(f"✅ Initial tokens monitoring completed: {result.get('activated', 0)} activated, {result.get('archived', 0)} archived")
                return result
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Monitor Initial tokens task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(bind=True, name="monitor_active_tokens_lifecycle")
def monitor_active_tokens_lifecycle_task(self) -> Dict[str, Any]:
    """
    Celery task для мониторинга жизненного цикла активных токенов
    
    Проверяет:
    - Низкий скор длительное время
    - Низкая активность в пулах
    
    Выполняется каждые 5 минут
    """
    try:
        logger.info("Starting Active tokens lifecycle monitoring...")
        
        from app.database import SessionLocal
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        db = SessionLocal()
        
        try:
            # Запускаем asyncio loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    lifecycle_manager.monitor_active_tokens_lifecycle(db)
                )
                
                logger.info(f"✅ Active tokens lifecycle completed: {result.get('deactivated', 0)} deactivated")
                return result
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Monitor Active tokens lifecycle task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(bind=True, name="fetch_metrics_for_initial_tokens")
def fetch_metrics_for_initial_tokens_task(self) -> Dict[str, Any]:
    """
    Celery task для получения метрик токенов в статусе Initial
    
    Выполняется реже чем для активных токенов (каждые 10 минут)
    """
    try:
        logger.info("Fetching metrics for Initial tokens...")
        
        from app.database import SessionLocal
        from app.crud import token_crud
        from app.models.token import TokenStatus
        from app.core.data_sources.birdeye_client import birdeye_manager
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        db = SessionLocal()
        
        try:
            # Получаем Initial токены
            initial_tokens = token_crud.get_by_status(
                db,
                status=TokenStatus.INITIAL,
                limit=200  # Больше лимит для Initial токенов
            )
            
            logger.info(f"Found {len(initial_tokens)} Initial tokens")
            
            if not initial_tokens:
                return {
                    "status": "success",
                    "tokens_processed": 0,
                    "message": "No Initial tokens found"
                }
            
            # Инициализируем Birdeye менеджер
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if not birdeye_manager.client:
                    loop.run_until_complete(birdeye_manager.initialize())
                
                # Обрабатываем токены с большей задержкой
                successful = 0
                failed = 0
                
                for token in initial_tokens:
                    try:
                        success = loop.run_until_complete(
                            birdeye_manager.save_token_metrics(token.token_address)
                        )
                        
                        if success:
                            successful += 1
                        else:
                            failed += 1
                        
                        # Большая задержка для Initial токенов (меньший приоритет)
                        loop.run_until_complete(asyncio.sleep(1.0))
                        
                    except Exception as e:
                        logger.error(f"Error processing Initial token {token.token_address}: {e}")
                        failed += 1
                
                return {
                    "status": "success",
                    "tokens_processed": len(initial_tokens),
                    "successful": successful,
                    "failed": failed,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Fetch metrics for Initial tokens task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="get_lifecycle_stats")
def get_lifecycle_stats_task() -> Dict[str, Any]:
    """
    Task для получения статистики жизненного цикла
    """
    try:
        from app.database import SessionLocal
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        db = SessionLocal()
        
        try:
            # Запускаем asyncio loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    lifecycle_manager.get_lifecycle_stats(db)
                )
                
                return result
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to get lifecycle stats: {e}")
        return {
            "error": str(e)
        }


@celery_app.task(bind=True, name="force_token_status_change")
def force_token_status_change_task(
    self, 
    token_address: str, 
    new_status: str, 
    reason: str = "manual",
    metadata: str = "Manual status change via admin"
) -> Dict[str, Any]:
    """
    Task для принудительного изменения статуса токена через админку
    
    Args:
        token_address: Адрес токена
        new_status: Новый статус (initial, active, archived)
        reason: Причина изменения
        metadata: Дополнительная информация
    """
    try:
        logger.info(f"Force status change for {token_address[:8]}... to {new_status}")
        
        from app.database import SessionLocal
        from app.crud import token_crud
        from app.models.token import TokenStatus, StatusChangeReason
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        # Валидация статуса
        try:
            target_status = TokenStatus(new_status.lower())
        except ValueError:
            return {
                "status": "error",
                "error": f"Invalid status: {new_status}. Valid: initial, active, archived"
            }
        
        # Валидация причины
        try:
            status_reason = StatusChangeReason(reason.lower())
        except ValueError:
            # Используем общую причину для ручных изменений
            status_reason = StatusChangeReason.DISCOVERY  # Fallback
        
        db = SessionLocal()
        
        try:
            # Находим токен
            token = token_crud.get_by_address(db, token_address=token_address)
            if not token:
                return {
                    "status": "error",
                    "error": f"Token {token_address} not found"
                }
            
            old_status = token.status
            
            if old_status == target_status:
                return {
                    "status": "success",
                    "message": f"Token already has status {new_status}",
                    "no_change": True
                }
            
            # Обновляем статус
            updated_token = token_crud.update_status(
                db,
                token=token,
                new_status=target_status,
                reason=status_reason,
                metadata=metadata
            )
            
            logger.info(
                f"✅ Token status changed: {token_address[:8]}... {old_status.value} -> {new_status}",
                extra={
                    "token_id": str(token.id),
                    "token_address": token_address,
                    "old_status": old_status.value,
                    "new_status": new_status,
                    "reason": reason,
                    "metadata": metadata,
                    "operation": "force_status_change"
                }
            )
            
            return {
                "status": "success",
                "token_address": token_address,
                "old_status": old_status.value,
                "new_status": new_status,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Force status change task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="cleanup_lifecycle_data")
def cleanup_lifecycle_data_task() -> Dict[str, Any]:
    """
    Task для очистки старых данных жизненного цикла
    
    Выполняется ежедневно
    """
    try:
        logger.info("Cleaning up lifecycle data...")
        
        from app.database import SessionLocal
        from app.models.token import TokenStatusHistory
        from app.crud.metrics import token_metrics_crud
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        db = SessionLocal()
        
        try:
            # Очищаем старые метрики (30 дней)
            old_metrics_cleaned = token_metrics_crud.cleanup_old_metrics(db, days_to_keep=30)
            
            # История статусов не очищается (нужна для аналитики)
            # Но можно добавить очистку очень старых записей (например, 1 год)
            
            logger.info(f"Lifecycle cleanup completed: {old_metrics_cleaned} old metrics cleaned")
            
            return {
                "status": "success",
                "old_metrics_cleaned": old_metrics_cleaned,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Cleanup lifecycle data task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
