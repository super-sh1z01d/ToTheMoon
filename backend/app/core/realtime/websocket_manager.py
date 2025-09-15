"""
WebSocket manager for real-time UI updates
Менеджер WebSocket соединений для real-time обновлений UI
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Set, Optional, List
from dataclasses import dataclass

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """
    Информация о WebSocket подключении
    """
    websocket: WebSocket
    client_id: str
    connected_at: datetime
    subscriptions: Set[str]
    
    async def send_message(self, message: Dict[str, Any]):
        """Отправка сообщения клиенту"""
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to {self.client_id}: {e}")


class WebSocketManager:
    """
    Менеджер WebSocket соединений для real-time обновлений
    
    Поддерживает:
    - Управление подключениями клиентов
    - Подписки на типы уведомлений
    - Broadcast сообщений
    - Мониторинг соединений
    """
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "connection_errors": 0,
            "started_at": datetime.now()
        }
        
    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        Установка WebSocket подключения
        """
        try:
            await websocket.accept()
            
            connection = WebSocketConnection(
                websocket=websocket,
                client_id=client_id,
                connected_at=datetime.now(),
                subscriptions=set()
            )
            
            self.connections[client_id] = connection
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)
            
            logger.info(
                f"WebSocket client connected: {client_id}",
                extra={
                    "client_id": client_id,
                    "active_connections": self.stats["active_connections"],
                    "operation": "websocket_connect"
                }
            )
            
            # Отправляем приветственное сообщение
            await self.send_to_client(client_id, {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "available_subscriptions": [
                    "token_updates",
                    "scoring_updates", 
                    "system_stats",
                    "celery_status",
                    "lifecycle_events"
                ]
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket client {client_id}: {e}")
            self.stats["connection_errors"] += 1
            return False
    
    async def disconnect(self, client_id: str):
        """
        Закрытие WebSocket подключения
        """
        try:
            if client_id in self.connections:
                connection = self.connections[client_id]
                
                # Закрываем соединение
                try:
                    await connection.websocket.close()
                except:
                    pass
                
                # Удаляем из списка
                del self.connections[client_id]
                self.stats["active_connections"] = len(self.connections)
                
                logger.info(
                    f"WebSocket client disconnected: {client_id}",
                    extra={
                        "client_id": client_id,
                        "active_connections": self.stats["active_connections"],
                        "operation": "websocket_disconnect"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket client {client_id}: {e}")
    
    async def subscribe(self, client_id: str, subscription_type: str) -> bool:
        """
        Подписка клиента на тип уведомлений
        """
        try:
            if client_id not in self.connections:
                return False
            
            connection = self.connections[client_id]
            connection.subscriptions.add(subscription_type)
            
            logger.debug(f"Client {client_id} subscribed to {subscription_type}")
            
            # Подтверждаем подписку
            await self.send_to_client(client_id, {
                "type": "subscription_confirmed",
                "subscription": subscription_type,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe {client_id} to {subscription_type}: {e}")
            return False
    
    async def unsubscribe(self, client_id: str, subscription_type: str) -> bool:
        """
        Отписка клиента от типа уведомлений
        """
        try:
            if client_id not in self.connections:
                return False
            
            connection = self.connections[client_id]
            connection.subscriptions.discard(subscription_type)
            
            logger.debug(f"Client {client_id} unsubscribed from {subscription_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe {client_id} from {subscription_type}: {e}")
            return False
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """
        Отправка сообщения конкретному клиенту
        """
        try:
            if client_id not in self.connections:
                return False
            
            connection = self.connections[client_id]
            await connection.send_message(message)
            
            self.stats["messages_sent"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            # Удаляем неисправное соединение
            await self.disconnect(client_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any], subscription_type: Optional[str] = None) -> int:
        """
        Broadcast сообщения всем подписанным клиентам
        """
        try:
            sent_count = 0
            failed_clients = []
            
            for client_id, connection in self.connections.items():
                try:
                    # Проверяем подписку если указан тип
                    if subscription_type and subscription_type not in connection.subscriptions:
                        continue
                    
                    await connection.send_message(message)
                    sent_count += 1
                    self.stats["messages_sent"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send broadcast to {client_id}: {e}")
                    failed_clients.append(client_id)
            
            # Очищаем неисправные соединения
            for client_id in failed_clients:
                await self.disconnect(client_id)
            
            if subscription_type:
                logger.debug(f"Broadcast '{subscription_type}' sent to {sent_count} clients")
            else:
                logger.debug(f"Broadcast sent to {sent_count} clients")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            return 0
    
    async def handle_client_message(self, client_id: str, message: str):
        """
        Обработка сообщений от клиентов
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                subscription = data.get("subscription")
                if subscription:
                    await self.subscribe(client_id, subscription)
                    
            elif message_type == "unsubscribe":
                subscription = data.get("subscription")
                if subscription:
                    await self.unsubscribe(client_id, subscription)
                    
            elif message_type == "ping":
                # Отвечаем на ping
                await self.send_to_client(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                logger.warning(f"Unknown message type from {client_id}: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
    
    async def send_token_update(self, token_data: Dict[str, Any]):
        """
        Отправка обновления токена всем подписанным клиентам
        """
        message = {
            "type": "token_update",
            "data": token_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.broadcast(message, "token_updates")
    
    async def send_scoring_update(self, scoring_data: Dict[str, Any]):
        """
        Отправка обновления скоринга
        """
        message = {
            "type": "scoring_update", 
            "data": scoring_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.broadcast(message, "scoring_updates")
    
    async def send_system_stats_update(self, stats_data: Dict[str, Any]):
        """
        Отправка обновления системной статистики
        """
        message = {
            "type": "system_stats_update",
            "data": stats_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.broadcast(message, "system_stats")
    
    async def send_lifecycle_event(self, event_data: Dict[str, Any]):
        """
        Отправка события жизненного цикла
        """
        message = {
            "type": "lifecycle_event",
            "data": event_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.broadcast(message, "lifecycle_events")
    
    def get_connections_info(self) -> List[Dict[str, Any]]:
        """
        Получение информации о подключениях
        """
        connections_info = []
        
        for client_id, connection in self.connections.items():
            connections_info.append({
                "client_id": client_id,
                "connected_at": connection.connected_at.isoformat(),
                "subscriptions": list(connection.subscriptions),
                "subscriptions_count": len(connection.subscriptions)
            })
        
        return connections_info
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики WebSocket manager
        """
        uptime = datetime.now() - self.stats["started_at"]
        
        return {
            **self.stats,
            "uptime_seconds": uptime.total_seconds(),
            "connections_info": self.get_connections_info()
        }
    
    async def cleanup_stale_connections(self):
        """
        Очистка устаревших соединений
        """
        stale_clients = []
        
        for client_id, connection in self.connections.items():
            try:
                # Проверяем соединение через ping
                await connection.websocket.ping()
            except Exception:
                stale_clients.append(client_id)
        
        # Удаляем неисправные соединения
        for client_id in stale_clients:
            await self.disconnect(client_id)
        
        logger.info(f"Cleaned up {len(stale_clients)} stale WebSocket connections")
        return len(stale_clients)


# Глобальный экземпляр менеджера
websocket_manager = WebSocketManager()
