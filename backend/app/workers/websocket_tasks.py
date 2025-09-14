"""
Celery tasks for WebSocket data collection
"""

import asyncio
import logging
from typing import Dict, Any

from celery import Celery
from app.core.data_sources.pumpportal_websocket import pumpportal_manager

logger = logging.getLogger(__name__)

# Создаем Celery app (будет переопределен в main celery config)
celery_app = Celery("websocket_tasks")


@celery_app.task(bind=True, name="start_pumpportal_websocket")
def start_pumpportal_websocket_task(self):
    """
    Celery task для запуска PumpPortal WebSocket клиента
    
    Этот task запускается как долгоживущий процесс
    """
    try:
        logger.info("Starting PumpPortal WebSocket task...")
        
        # Запускаем asyncio loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(pumpportal_manager.start())
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"PumpPortal WebSocket task failed: {e}")
        raise


@celery_app.task(name="get_pumpportal_stats")
def get_pumpportal_stats() -> Dict[str, Any]:
    """
    Task для получения статистики PumpPortal WebSocket
    """
    try:
        return pumpportal_manager.get_stats()
    except Exception as e:
        logger.error(f"Failed to get PumpPortal stats: {e}")
        return {
            "error": str(e),
            "connected": False,
            "running": False
        }


@celery_app.task(name="stop_pumpportal_websocket")
def stop_pumpportal_websocket_task():
    """
    Task для остановки PumpPortal WebSocket клиента
    """
    try:
        logger.info("Stopping PumpPortal WebSocket task...")
        
        # Создаем новый event loop для остановки
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(pumpportal_manager.stop())
        finally:
            loop.close()
            
        logger.info("PumpPortal WebSocket task stopped")
        
    except Exception as e:
        logger.error(f"Error stopping PumpPortal WebSocket: {e}")
        raise
