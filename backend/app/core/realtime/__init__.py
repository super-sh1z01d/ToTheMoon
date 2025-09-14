"""
Real-time updates system for ToTheMoon2
Система real-time обновлений
"""

from .websocket_manager import WebSocketManager, websocket_manager
from .notifications import NotificationManager, notification_manager

__all__ = [
    "WebSocketManager",
    "websocket_manager",
    "NotificationManager", 
    "notification_manager"
]
