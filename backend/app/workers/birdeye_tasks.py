"""
Celery tasks for Birdeye API data collection
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from celery import Celery
from app.core.data_sources.birdeye_client import birdeye_manager

logger = logging.getLogger(__name__)

# Создаем Celery app (будет переопределен в main celery config)
celery_app = Celery("birdeye_tasks")


@celery_app.task(bind=True, name="fetch_token_metrics")
def fetch_token_metrics_task(self, token_address: str) -> Dict[str, Any]:
    """
    Celery task для получения метрик токена от Birdeye API
    
    Args:
        token_address: Адрес токена Solana
        
    Returns:
        Dict с результатом операции
    """
    try:
        logger.info(f"Fetching metrics for token {token_address[:8]}...")
        
        # Запускаем asyncio loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Инициализируем менеджер если нужно
            if not birdeye_manager.client:
                loop.run_until_complete(birdeye_manager.initialize())
            
            # Получаем и сохраняем метрики
            success = loop.run_until_complete(
                birdeye_manager.save_token_metrics(token_address)
            )
            
            if success:
                logger.info(f"✅ Metrics fetched and saved for {token_address[:8]}...")
                return {
                    "status": "success",
                    "token_address": token_address,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning(f"⚠️  Failed to fetch metrics for {token_address[:8]}...")
                return {
                    "status": "failed",
                    "token_address": token_address,
                    "error": "Failed to fetch or save metrics"
                }
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Birdeye metrics task failed for {token_address}: {e}")
        return {
            "status": "error",
            "token_address": token_address,
            "error": str(e)
        }


@celery_app.task(bind=True, name="fetch_metrics_for_active_tokens")
def fetch_metrics_for_active_tokens_task(self) -> Dict[str, Any]:
    """
    Celery task для получения метрик всех активных токенов
    
    Выполняется по расписанию (например, каждые 2 минуты)
    """
    try:
        logger.info("Fetching metrics for all active tokens...")
        
        # Получаем список активных токенов
        from app.database import SessionLocal
        from app.crud import token_crud
        from app.models.token import TokenStatus
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        db = SessionLocal()
        
        try:
            # Получаем активные токены
            active_tokens = token_crud.get_by_status(
                db, 
                status=TokenStatus.ACTIVE,
                limit=100  # Ограничиваем для rate limits
            )
            
            logger.info(f"Found {len(active_tokens)} active tokens")
            
            if not active_tokens:
                return {
                    "status": "success",
                    "tokens_processed": 0,
                    "message": "No active tokens found"
                }
            
            # Инициализируем Birdeye менеджер
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if not birdeye_manager.client:
                    loop.run_until_complete(birdeye_manager.initialize())
                
                # Обрабатываем токены с задержкой для rate limits
                successful = 0
                failed = 0
                
                for token in active_tokens:
                    try:
                        success = loop.run_until_complete(
                            birdeye_manager.save_token_metrics(token.token_address)
                        )
                        
                        if success:
                            successful += 1
                        else:
                            failed += 1
                        
                        # Небольшая задержка между запросами  
                        loop.run_until_complete(asyncio.sleep(0.5))
                        
                    except Exception as e:
                        logger.error(f"Error processing token {token.token_address}: {e}")
                        failed += 1
                
                return {
                    "status": "success",
                    "tokens_processed": len(active_tokens),
                    "successful": successful,
                    "failed": failed,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Fetch metrics for active tokens task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="cleanup_old_birdeye_data")
def cleanup_old_birdeye_data_task() -> Dict[str, Any]:
    """
    Task для очистки устаревших данных Birdeye
    
    Выполняется ежедневно
    """
    try:
        logger.info("Cleaning up old Birdeye data...")
        
        from app.database import SessionLocal
        from app.crud.metrics import birdeye_raw_data_crud, token_metrics_crud
        
        if not SessionLocal:
            logger.error("Database not configured")
            return {"status": "error", "error": "Database not configured"}
        
        db = SessionLocal()
        
        try:
            # Очистка expired raw данных
            expired_raw = birdeye_raw_data_crud.cleanup_expired_data(db)
            
            # Очистка старых метрик (30 дней)
            old_metrics = token_metrics_crud.cleanup_old_metrics(db, days_to_keep=30)
            
            logger.info(f"Cleanup completed: {expired_raw} raw data, {old_metrics} metrics")
            
            return {
                "status": "success",
                "expired_raw_data_cleaned": expired_raw,
                "old_metrics_cleaned": old_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="get_birdeye_stats")
def get_birdeye_stats_task() -> Dict[str, Any]:
    """
    Task для получения статистики Birdeye API
    """
    try:
        stats = birdeye_manager.get_stats()
        
        # Добавляем статистику БД
        from app.database import SessionLocal
        from app.crud.metrics import birdeye_raw_data_crud
        
        if SessionLocal:
            db = SessionLocal()
            try:
                db_stats = birdeye_raw_data_crud.get_storage_stats(db)
                stats.update({"storage": db_stats})
            finally:
                db.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get Birdeye stats: {e}")
        return {
            "error": str(e),
            "client_initialized": False
        }


@celery_app.task(bind=True, name="test_birdeye_connection")
def test_birdeye_connection_task(self) -> Dict[str, Any]:
    """
    Task для тестирования подключения к Birdeye API
    """
    try:
        logger.info("Testing Birdeye API connection...")
        
        # Тестируем с известным токеном (SOL)
        test_token = "So11111111111111111111111111111111111111112"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Инициализируем менеджер
            if not birdeye_manager.client:
                loop.run_until_complete(birdeye_manager.initialize())
            
            # Тестируем получение данных
            metrics = loop.run_until_complete(
                birdeye_manager.fetch_token_metrics(test_token)
            )
            
            if metrics:
                logger.info("✅ Birdeye API connection test successful")
                return {
                    "status": "success",
                    "test_token": test_token,
                    "data_received": bool(metrics),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("⚠️  Birdeye API test failed - no data received")
                return {
                    "status": "failed",
                    "test_token": test_token,
                    "error": "No data received"
                }
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Birdeye connection test failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
