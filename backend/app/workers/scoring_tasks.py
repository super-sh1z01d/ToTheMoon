"""
Celery tasks for scoring calculations
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from celery import Celery
from app.core.scoring.manager import scoring_manager

logger = logging.getLogger(__name__)

# Создаем Celery app (будет переопределен в main celery config)
celery_app = Celery("scoring_tasks")


@celery_app.task(bind=True, name="calculate_token_score")
def calculate_token_score_task(self, token_address: str) -> Dict[str, Any]:
    """
    Celery task для расчета скора конкретного токена
    
    Args:
        token_address: Адрес токена Solana
        
    Returns:
        Dict с результатом операции
    """
    try:
        logger.info(f"Calculating score for token {token_address[:8]}...")
        
        # Получаем сессию БД
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
                    scoring_manager.calculate_score_for_token(token_address, db)
                )
                
                if result:
                    logger.info(f"✅ Score calculated for {token_address[:8]}...: {result.score_smoothed:.3f}")
                    return {
                        "status": "success",
                        "token_address": token_address,
                        "score_value": result.score_value,
                        "score_smoothed": result.score_smoothed,
                        "model_name": result.model_name,
                        "execution_time_ms": result.execution_time_ms,
                        "timestamp": result.timestamp.isoformat()
                    }
                else:
                    logger.warning(f"⚠️  No score calculated for {token_address[:8]}...")
                    return {
                        "status": "failed",
                        "token_address": token_address,
                        "error": "No score calculated"
                    }
                    
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Score calculation task failed for {token_address}: {e}")
        return {
            "status": "error",
            "token_address": token_address,
            "error": str(e)
        }


@celery_app.task(bind=True, name="calculate_scores_for_active_tokens")
def calculate_scores_for_active_tokens_task(self) -> Dict[str, Any]:
    """
    Celery task для расчета скоров всех активных токенов
    
    Выполняется по расписанию (например, каждые 2 минуты)
    """
    try:
        logger.info("Calculating scores for all active tokens...")
        
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
                    scoring_manager.calculate_scores_for_active_tokens(db)
                )
                
                logger.info(f"✅ Scores calculated: {result.get('successful', 0)} successful, {result.get('failed', 0)} failed")
                return result
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Calculate scores for active tokens task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="reload_scoring_model")
def reload_scoring_model_task() -> Dict[str, Any]:
    """
    Task для перезагрузки модели скоринга
    
    Используется при изменении конфигурации
    """
    try:
        logger.info("Reloading scoring model...")
        
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
                success = loop.run_until_complete(
                    scoring_manager.reload_model(db)
                )
                
                if success:
                    logger.info("✅ Scoring model reloaded successfully")
                    return {
                        "status": "success",
                        "message": "Scoring model reloaded",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.error("❌ Failed to reload scoring model")
                    return {
                        "status": "failed",
                        "error": "Failed to reload model"
                    }
                    
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Reload scoring model task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="test_scoring_model")
def test_scoring_model_task(test_token_address: str = "So11111111111111111111111111111111111111112") -> Dict[str, Any]:
    """
    Task для тестирования модели скоринга
    
    Args:
        test_token_address: Адрес токена для тестирования (по умолчанию SOL)
    """
    try:
        logger.info(f"Testing scoring model with token {test_token_address[:8]}...")
        
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
                    scoring_manager.test_model_calculation(test_token_address, db)
                )
                
                logger.info(f"✅ Scoring model test completed")
                return result
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Test scoring model task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="get_scoring_stats")
def get_scoring_stats_task() -> Dict[str, Any]:
    """
    Task для получения статистики скоринга
    """
    try:
        stats = scoring_manager.get_stats()
        
        # Добавляем статистику из БД
        from app.database import SessionLocal
        from app.crud.metrics import token_scores_crud
        
        if SessionLocal:
            db = SessionLocal()
            try:
                from app.models.metrics import TokenScores
                
                # Общее количество скоров
                total_scores = db.query(TokenScores).count()
                
                # Последние скоры
                latest_scores = db.query(TokenScores).order_by(
                    TokenScores.calculated_at.desc()
                ).limit(5).all()
                
                latest_scores_data = []
                for score in latest_scores:
                    latest_scores_data.append({
                        "token_id": str(score.token_id),
                        "model_name": score.model_name,
                        "score_value": score.score_value,
                        "calculated_at": score.calculated_at.isoformat()
                    })
                
                stats.update({
                    "database": {
                        "total_scores": total_scores,
                        "latest_scores": latest_scores_data
                    }
                })
                
            finally:
                db.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get scoring stats: {e}")
        return {
            "error": str(e),
            "model_loaded": False
        }
