"""
Notification manager for real-time updates
Менеджер уведомлений для real-time обновлений через Redis Pub/Sub
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Менеджер уведомлений для real-time системы
    
    Использует Redis Pub/Sub для отправки уведомлений:
    - Изменения токенов
    - Обновления скоров
    - События жизненного цикла
    - Системная статистика
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub = None
        self.channels = {
            "token_updates": "tothemoon:tokens",
            "scoring_updates": "tothemoon:scoring", 
            "lifecycle_events": "tothemoon:lifecycle",
            "system_stats": "tothemoon:stats",
            "celery_status": "tothemoon:celery"
        }
        
        self.stats = {
            "notifications_sent": 0,
            "redis_errors": 0,
            "subscribers_count": 0,
            "last_notification": None
        }
    
    async def initialize(self):
        """
        Инициализация Redis подключения
        """
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Проверяем подключение
            await self.redis_client.ping()
            
            logger.info("✅ Notification manager initialized with Redis")
            
        except Exception as e:
            logger.error(f"Failed to initialize notification manager: {e}")
            self.redis_client = None
    
    async def close(self):
        """
        Закрытие Redis подключения
        """
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Notification manager closed")
    
    async def publish_token_update(
        self, 
        token_address: str, 
        update_type: str,
        data: Dict[str, Any]
    ):
        """
        Публикация обновления токена
        """
        notification = {
            "type": "token_update",
            "update_type": update_type,  # "status_changed", "score_updated", "created"
            "token_address": token_address,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._publish_notification("token_updates", notification)
    
    async def publish_scoring_update(
        self,
        token_address: str,
        score_data: Dict[str, Any]
    ):
        """
        Публикация обновления скора
        """
        notification = {
            "type": "scoring_update",
            "token_address": token_address,
            "data": score_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._publish_notification("scoring_updates", notification)
    
    async def publish_lifecycle_event(
        self,
        event_type: str,
        token_address: str,
        event_data: Dict[str, Any]
    ):
        """
        Публикация события жизненного цикла
        """
        notification = {
            "type": "lifecycle_event",
            "event_type": event_type,  # "activated", "archived", "deactivated"
            "token_address": token_address,
            "data": event_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._publish_notification("lifecycle_events", notification)
    
    async def publish_system_stats(self, stats_data: Dict[str, Any]):
        """
        Публикация системной статистики
        """
        notification = {
            "type": "system_stats",
            "data": stats_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._publish_notification("system_stats", notification)
    
    async def publish_celery_status(self, celery_data: Dict[str, Any]):
        """
        Публикация статуса Celery
        """
        notification = {
            "type": "celery_status",
            "data": celery_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._publish_notification("celery_status", notification)
    
    async def _publish_notification(self, channel_type: str, notification: Dict[str, Any]):
        """
        Внутренний метод для публикации уведомлений
        """
        try:
            if not self.redis_client:
                logger.warning("Redis not available for notifications")
                return
            
            channel = self.channels.get(channel_type)
            if not channel:
                logger.error(f"Unknown notification channel: {channel_type}")
                return
            
            # Публикуем в Redis
            await self.redis_client.publish(channel, json.dumps(notification))
            
            self.stats["notifications_sent"] += 1
            self.stats["last_notification"] = datetime.now()
            
            logger.debug(
                f"Published {channel_type} notification",
                extra={
                    "channel": channel,
                    "notification_type": notification.get("type"),
                    "operation": "notification_published"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to publish notification to {channel_type}: {e}")
            self.stats["redis_errors"] += 1
    
    async def start_subscriber(self, websocket_manager):
        """
        Запуск подписчика Redis для пересылки уведомлений в WebSocket
        """
        try:
            if not self.redis_client:
                logger.error("Cannot start subscriber without Redis")
                return
            
            # Создаем pubsub
            self.pubsub = self.redis_client.pubsub()
            
            # Подписываемся на все каналы
            for channel in self.channels.values():
                await self.pubsub.subscribe(channel)
            
            logger.info(f"Started Redis subscriber for {len(self.channels)} channels")
            
            # Основной цикл обработки сообщений
            async for message in self.pubsub.listen():
                try:
                    if message["type"] == "message":
                        # Парсим уведомление
                        notification = json.loads(message["data"])
                        channel = message["channel"]
                        
                        # Определяем тип подписки
                        subscription_type = None
                        for sub_type, sub_channel in self.channels.items():
                            if sub_channel == channel:
                                subscription_type = sub_type
                                break
                        
                        if subscription_type:
                            # Пересылаем в WebSocket manager
                            await websocket_manager.broadcast(notification, subscription_type)
                            
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
                    
        except Exception as e:
            logger.error(f"Redis subscriber failed: {e}")
        finally:
            if self.pubsub:
                await self.pubsub.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики уведомлений
        """
        return {
            **self.stats,
            "redis_connected": self.redis_client is not None,
            "active_channels": len(self.channels),
            "channels": list(self.channels.keys())
        }


# Глобальный экземпляр менеджера
notification_manager = NotificationManager()
