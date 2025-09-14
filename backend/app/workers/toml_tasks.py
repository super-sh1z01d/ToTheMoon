"""
Celery tasks for TOML export generation
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from celery import Celery
from app.core.toml_export.generator import toml_generator

logger = logging.getLogger(__name__)

# Создаем Celery app (будет переопределен в main celery config)
celery_app = Celery("toml_tasks")


@celery_app.task(bind=True, name="generate_toml_config")
def generate_toml_config_task(self) -> Dict[str, Any]:
    """
    Celery task для генерации TOML конфигурации
    
    Может выполняться по расписанию для предварительной генерации
    """
    try:
        logger.info("Generating TOML config...")
        
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
                toml_content = loop.run_until_complete(
                    toml_generator.generate_dynamic_strategy_toml(db)
                )
                
                # Анализируем результат
                import toml
                parsed_config = toml.loads(toml_content)
                
                tokens_count = len(parsed_config.get("tokens", []))
                
                logger.info(f"✅ TOML config generated with {tokens_count} tokens")
                
                return {
                    "status": "success",
                    "tokens_count": tokens_count,
                    "config_size_bytes": len(toml_content.encode('utf-8')),
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Generate TOML config task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="validate_toml_export")
def validate_toml_export_task() -> Dict[str, Any]:
    """
    Task для валидации конфигурации TOML экспорта
    
    Проверяет корректность параметров и наличие подходящих токенов
    """
    try:
        logger.info("Validating TOML export configuration...")
        
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
                validation_result = loop.run_until_complete(
                    toml_generator.validate_export_config(db)
                )
                
                if validation_result["valid"]:
                    logger.info("✅ TOML export configuration is valid")
                else:
                    logger.warning(f"⚠️ TOML export configuration issues: {validation_result['issues']}")
                
                return {
                    "status": "success",
                    "validation": validation_result,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Validate TOML export task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="get_toml_export_stats")
def get_toml_export_stats_task() -> Dict[str, Any]:
    """
    Task для получения статистики TOML экспорта
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
                # Получаем статистику генератора
                generator_stats = toml_generator.get_stats()
                
                # Получаем предварительный просмотр
                preview = loop.run_until_complete(
                    toml_generator.get_export_preview(db)
                )
                
                # Валидация конфигурации
                validation = loop.run_until_complete(
                    toml_generator.validate_export_config(db)
                )
                
                return {
                    "status": "success",
                    "generator_stats": generator_stats,
                    "export_preview": preview,
                    "config_validation": validation,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Get TOML export stats task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(bind=True, name="test_toml_generation")
def test_toml_generation_task(
    self,
    min_score: float = 0.5,
    top_count: int = 3
) -> Dict[str, Any]:
    """
    Task для тестирования генерации TOML
    
    Args:
        min_score: Минимальный скор для тестирования
        top_count: Количество токенов для тестирования
    """
    try:
        logger.info(f"Testing TOML generation with min_score={min_score}, top_count={top_count}")
        
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
                # Тестовая генерация
                toml_content = loop.run_until_complete(
                    toml_generator.generate_custom_toml(
                        db,
                        min_score=min_score,
                        top_count=top_count
                    )
                )
                
                # Парсим результат для валидации
                import toml
                parsed_config = toml.loads(toml_content)
                
                tokens_count = len(parsed_config.get("tokens", []))
                
                logger.info(f"✅ TOML test generation successful: {tokens_count} tokens")
                
                return {
                    "status": "success",
                    "tokens_count": tokens_count,
                    "config_size_bytes": len(toml_content.encode('utf-8')),
                    "min_score_used": min_score,
                    "top_count_used": top_count,
                    "toml_preview": toml_content[:500] + "..." if len(toml_content) > 500 else toml_content,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Test TOML generation task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
