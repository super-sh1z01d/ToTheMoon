"""
Real-time WebSocket endpoints for UI updates
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.realtime.websocket_manager import websocket_manager
from app.core.realtime.notifications import notification_manager

router = APIRouter(prefix="/realtime", tags=["realtime"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для real-time обновлений UI
    
    Поддерживает подписки на:
    - token_updates: обновления токенов
    - scoring_updates: обновления скоров
    - system_stats: системная статистика
    - lifecycle_events: события жизненного цикла
    - celery_status: статус Celery workers
    """
    client_id = str(uuid.uuid4())
    
    try:
        # Устанавливаем соединение
        if not await websocket_manager.connect(websocket, client_id):
            await websocket.close(code=1011, reason="Connection failed")
            return
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение от клиента
                message = await websocket.receive_text()
                
                # Обрабатываем сообщение
                await websocket_manager.handle_client_message(client_id, message)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop for {client_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        # Закрываем соединение
        await websocket_manager.disconnect(client_id)


@router.get("/connections")
async def get_websocket_connections() -> Dict[str, Any]:
    """
    Получить информацию о WebSocket подключениях
    """
    try:
        connections_info = websocket_manager.get_connections_info()
        stats = websocket_manager.get_stats()
        
        return {
            "connections": connections_info,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get connections info", "details": {"error": str(e)}})


@router.post("/test-notification")
async def send_test_notification(
    notification_type: str,
    test_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Отправка тестового уведомления для проверки WebSocket
    """
    try:
        if test_data is None:
            test_data = {
                "message": "Test notification",
                "timestamp": datetime.now().isoformat()
            }
        
        # Отправляем через notification manager
        if notification_type == "token_updates":
            await notification_manager.publish_token_update(
                "TestToken111111111111111111111111111111",
                "test_update",
                test_data
            )
        elif notification_type == "scoring_updates":
            await notification_manager.publish_scoring_update(
                "TestToken111111111111111111111111111111",
                test_data
            )
        elif notification_type == "system_stats":
            await notification_manager.publish_system_stats(test_data)
        elif notification_type == "lifecycle_events":
            await notification_manager.publish_lifecycle_event(
                "test_event",
                "TestToken111111111111111111111111111111",
                test_data
            )
        else:
            raise HTTPException(status_code=400, detail={"message": "Unknown notification type", "details": {"given": notification_type}})
        
        return {
            "message": f"Test notification '{notification_type}' sent",
            "data": test_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to send test notification", "details": {"error": str(e)}})


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    subscription_type: str = None
) -> Dict[str, Any]:
    """
    Broadcast сообщения всем WebSocket клиентам
    """
    try:
        sent_count = await websocket_manager.broadcast(message, subscription_type)
        
        return {
            "message": "Broadcast sent successfully",
            "sent_to_clients": sent_count,
            "subscription_type": subscription_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to broadcast message", "details": {"error": str(e)}})


@router.get("/stats")
async def get_realtime_stats() -> Dict[str, Any]:
    """
    Получить статистику real-time системы
    """
    try:
        websocket_stats = websocket_manager.get_stats()
        notification_stats = notification_manager.get_stats()
        
        return {
            "websocket_manager": websocket_stats,
            "notification_manager": notification_stats,
            "total_active_connections": len(websocket_manager.connections),
            "available_channels": list(notification_manager.channels.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get realtime stats", "details": {"error": str(e)}})


@router.post("/cleanup-connections")
async def cleanup_stale_connections() -> Dict[str, Any]:
    """
    Очистка устаревших WebSocket соединений
    """
    try:
        cleaned_count = await websocket_manager.cleanup_stale_connections()
        
        return {
            "message": f"Cleaned up {cleaned_count} stale connections",
            "cleaned_count": cleaned_count,
            "active_connections": len(websocket_manager.connections),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to cleanup connections", "details": {"error": str(e)}})


@router.get("/health")
async def get_realtime_health() -> Dict[str, Any]:
    """
    Проверка здоровья real-time системы
    """
    try:
        # Проверяем Redis подключение
        redis_healthy = False
        if notification_manager.redis_client:
            try:
                await notification_manager.redis_client.ping()
                redis_healthy = True
            except:
                pass
        
        # Статистика WebSocket соединений
        websocket_healthy = len(websocket_manager.connections) >= 0  # Всегда true, но логика для расширения
        
        overall_status = "healthy"
        issues = []
        
        if not redis_healthy:
            overall_status = "degraded"
            issues.append("Redis connection failed")
        
        if not websocket_healthy:
            overall_status = "degraded"
            issues.append("WebSocket manager issues")
        
        return {
            "status": overall_status,
            "issues": issues,
            "components": {
                "redis": "healthy" if redis_healthy else "unhealthy",
                "websocket_manager": "healthy" if websocket_healthy else "unhealthy"
            },
            "active_connections": len(websocket_manager.connections),
            "redis_channels": len(notification_manager.channels),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to check realtime health", "details": {"error": str(e)}})
