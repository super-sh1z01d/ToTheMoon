"""
WebSocket management endpoints
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.core.data_sources.pumpportal_websocket import pumpportal_manager
from app.workers.websocket_tasks import (
    start_pumpportal_websocket_task,
    stop_pumpportal_websocket_task,
    get_pumpportal_stats
)

router = APIRouter(prefix="/websocket", tags=["websocket"])


@router.get("/pumpportal/status")
async def get_pumpportal_status() -> Dict[str, Any]:
    """
    Получить статус PumpPortal WebSocket подключения
    """
    try:
        stats = pumpportal_manager.get_stats()
        return {
            "status": "connected" if stats.get("connected") else "disconnected",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting PumpPortal status", "details": {"error": str(e)}})


@router.post("/pumpportal/start")
async def start_pumpportal():
    """
    Запустить PumpPortal WebSocket подключение
    """
    try:
        # Проверяем текущий статус
        if pumpportal_manager._running:
            return {
                "message": "PumpPortal WebSocket already running",
                "status": "already_running"
            }
        
        # Запускаем task в Celery
        task = start_pumpportal_websocket_task.delay()
        
        return {
            "message": "PumpPortal WebSocket start initiated",
            "task_id": task.id,
            "status": "starting"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error starting PumpPortal", "details": {"error": str(e)}})


@router.post("/pumpportal/stop")
async def stop_pumpportal():
    """
    Остановить PumpPortal WebSocket подключение
    """
    try:
        # Останавливаем через task
        task = stop_pumpportal_websocket_task.delay()
        
        return {
            "message": "PumpPortal WebSocket stop initiated", 
            "task_id": task.id,
            "status": "stopping"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error stopping PumpPortal", "details": {"error": str(e)}})


@router.get("/stats")
async def get_websocket_stats() -> Dict[str, Any]:
    """
    Получить общую статистику WebSocket интеграций
    """
    try:
        stats = {
            "pumpportal": pumpportal_manager.get_stats(),
            "timestamp": int(datetime.now().timestamp())
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting WebSocket stats", "details": {"error": str(e)}})


@router.post("/pumpportal/test")
async def test_pumpportal_connection():
    """
    Тестовое подключение к PumpPortal (для отладки)
    """
    try:
        from app.core.data_sources.pumpportal_websocket import PumpPortalWebSocketClient
        
        # Создаем временный клиент для теста
        test_client = PumpPortalWebSocketClient()
        
        connected = await test_client.connect()
        
        if connected:
            await test_client.disconnect()
            return {
                "status": "success",
                "message": "PumpPortal WebSocket connection test successful"
            }
        else:
            return {
                "status": "failed", 
                "message": "Failed to connect to PumpPortal WebSocket"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error testing PumpPortal connection", "details": {"error": str(e)}})
