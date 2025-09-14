"""
PumpPortal WebSocket client for token discovery
Интеграция с wss://pumpportal.fun/api/data
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException


logger = logging.getLogger(__name__)


@dataclass
class TokenMigrationEvent:
    """
    Событие миграции токена с pump.fun
    """
    token_address: str
    timestamp: datetime
    liquidity_pool_address: Optional[str] = None
    dex_name: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class NewTokenEvent:
    """
    Событие создания нового токена на pump.fun
    """
    token_address: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    timestamp: datetime = None
    raw_data: Optional[Dict[str, Any]] = None


class PumpPortalWebSocketClient:
    """
    WebSocket клиент для получения данных от PumpPortal
    
    Поддерживает:
    - subscribeMigration - миграции токенов с pump.fun на Raydium
    - subscribeNewToken - новые токены на pump.fun
    - Автоматический reconnect при обрывах
    - Graceful shutdown
    """
    
    def __init__(
        self,
        websocket_url: Optional[str] = None,
        on_migration: Optional[Callable[[TokenMigrationEvent], None]] = None,
        on_new_token: Optional[Callable[[NewTokenEvent], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        max_reconnect_attempts: int = 5,
        reconnect_delay: int = 5
    ):
        self.websocket_url = websocket_url or os.getenv(
            "PUMPPORTAL_WS_URL",
            # Актуальный endpoint real-time API
            "wss://pumpportal.fun/data-api/real-time",
        )
        
        # Event handlers
        self.on_migration = on_migration
        self.on_new_token = on_new_token  
        self.on_error = on_error
        
        # Connection settings
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        # State
        self._websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._running = False
        self._reconnect_count = 0
        self._subscriptions: List[Dict[str, Any]] = []
        
        logger.info(f"PumpPortal WebSocket client initialized: {self.websocket_url}")

    async def connect(self) -> bool:
        """
        Подключение к WebSocket
        """
        try:
            logger.info("Connecting to PumpPortal WebSocket...")
            
            self._websocket = await websockets.connect(
                self.websocket_url,
                ping_interval=30,  # Поддержание соединения
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.info("✅ Connected to PumpPortal WebSocket")
            self._reconnect_count = 0
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to PumpPortal: {e}")
            if self.on_error:
                self.on_error(e)
            return False

    async def disconnect(self):
        """
        Отключение от WebSocket
        """
        self._running = False
        
        if self._websocket:
            logger.info("Disconnecting from PumpPortal WebSocket...")
            await self._websocket.close()
            self._websocket = None
            
        logger.info("Disconnected from PumpPortal WebSocket")

    async def subscribe_migrations(self) -> bool:
        """
        Подписка на события миграции токенов
        """
        payload = {
            "method": "subscribeMigration"
        }
        
        try:
            if not self._websocket:
                logger.error("WebSocket not connected")
                return False
                
            await self._websocket.send(json.dumps(payload))
            self._subscriptions.append(payload)
            
            logger.info("✅ Subscribed to migration events")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to migrations: {e}")
            if self.on_error:
                self.on_error(e)
            return False

    async def subscribe_new_tokens(self) -> bool:
        """
        Подписка на события создания новых токенов
        """
        payload = {
            "method": "subscribeNewToken"
        }
        
        try:
            if not self._websocket:
                logger.error("WebSocket not connected")
                return False
                
            await self._websocket.send(json.dumps(payload))
            self._subscriptions.append(payload)
            
            logger.info("✅ Subscribed to new token events")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to new tokens: {e}")
            if self.on_error:
                self.on_error(e)
            return False

    async def _resubscribe(self):
        """
        Повторная подписка после переподключения
        """
        logger.info("Re-subscribing to events...")
        
        for subscription in self._subscriptions:
            try:
                await self._websocket.send(json.dumps(subscription))
                logger.info(f"Re-subscribed to {subscription['method']}")
            except Exception as e:
                logger.error(f"Failed to re-subscribe to {subscription['method']}: {e}")

    def _parse_migration_event(self, data: Dict[str, Any]) -> Optional[TokenMigrationEvent]:
        """
        Парсинг события миграции токена
        """
        try:
            # Пример структуры данных от PumpPortal (может отличаться)
            token_address = data.get("mint") or data.get("token_address")
            liquidity_pool = data.get("pool_address") or data.get("liquidity_pool_address")
            
            if not token_address:
                logger.warning("Migration event without token address")
                return None
                
            return TokenMigrationEvent(
                token_address=token_address,
                timestamp=datetime.now(),
                liquidity_pool_address=liquidity_pool,
                dex_name="raydium",  # Обычно миграции идут на Raydium
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Failed to parse migration event: {e}")
            logger.debug(f"Raw data: {data}")
            return None

    def _parse_new_token_event(self, data: Dict[str, Any]) -> Optional[NewTokenEvent]:
        """
        Парсинг события создания нового токена
        """
        try:
            token_address = data.get("mint") or data.get("token_address")
            name = data.get("name")
            symbol = data.get("symbol")
            
            if not token_address:
                logger.warning("New token event without token address")
                return None
                
            return NewTokenEvent(
                token_address=token_address,
                name=name,
                symbol=symbol,
                timestamp=datetime.now(),
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Failed to parse new token event: {e}")
            logger.debug(f"Raw data: {data}")
            return None

    async def _handle_message(self, message: str):
        """
        Обработка входящих сообщений WebSocket
        """
        try:
            data = json.loads(message)
            
            # Определяем тип события
            event_type = data.get("type") or data.get("event")

            # Игнорируем сообщения подтверждений подписки
            method = data.get("method")
            if method in {"subscribeMigration", "subscribeNewToken"}:
                logger.debug(f"Subscription ack received: {method}")
                return

            if event_type == "migration":
                # Событие миграции
                if self.on_migration:
                    migration_event = self._parse_migration_event(data)
                    if migration_event:
                        self.on_migration(migration_event)

            elif event_type == "newToken":
                # Событие нового токена
                if self.on_new_token:
                    new_token_event = self._parse_new_token_event(data)
                    if new_token_event:
                        self.on_new_token(new_token_event)

            else:
                # Логируем неизвестные события для отладки
                logger.debug(f"Unknown event type: {event_type}")
                logger.debug(f"Raw message: {message[:200]}...")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
            logger.debug(f"Raw message: {message[:200]}...")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            logger.debug(f"Raw message: {message[:200]}...")

    async def _listen_loop(self):
        """
        Основной цикл прослушивания WebSocket
        """
        try:
            async for message in self._websocket:
                if not self._running:
                    break
                    
                await self._handle_message(message)
                
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            if self.on_error:
                self.on_error(e)
                
        except Exception as e:
            logger.error(f"Unexpected error in listen loop: {e}")
            if self.on_error:
                self.on_error(e)

    async def start(self, subscribe_migrations: bool = True, subscribe_new_tokens: bool = False):
        """
        Запуск WebSocket клиента с подписками
        
        Args:
            subscribe_migrations: Подписаться на миграции токенов
            subscribe_new_tokens: Подписаться на новые токены
        """
        self._running = True
        
        while self._running and self._reconnect_count < self.max_reconnect_attempts:
            try:
                # Подключение
                connected = await self.connect()
                if not connected:
                    await self._handle_reconnect()
                    continue
                
                # Подписки
                subscription_success = True
                
                if subscribe_migrations:
                    if not await self.subscribe_migrations():
                        subscription_success = False
                
                if subscribe_new_tokens:
                    if not await self.subscribe_new_tokens():
                        subscription_success = False
                
                if not subscription_success:
                    logger.error("Failed to set up subscriptions")
                    await self._handle_reconnect()
                    continue
                
                # Запуск основного цикла
                logger.info("🎧 Starting WebSocket message loop...")
                await self._listen_loop()
                
                # Если дошли сюда, значит соединение разорвалось
                if self._running:  # Если не было явного stop()
                    await self._handle_reconnect()
                    
            except Exception as e:
                logger.error(f"Error in WebSocket client: {e}")
                if self.on_error:
                    self.on_error(e)
                    
                if self._running:
                    await self._handle_reconnect()

    async def _handle_reconnect(self):
        """
        Обработка переподключения
        """
        if self._reconnect_count >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached, stopping")
            self._running = False
            return
            
        self._reconnect_count += 1
        logger.info(f"Attempting reconnect {self._reconnect_count}/{self.max_reconnect_attempts} in {self.reconnect_delay}s...")
        
        # Закрываем текущее соединение
        if self._websocket:
            try:
                await self._websocket.close()
            except:
                pass
            self._websocket = None
        
        # Ждем перед переподключением
        await asyncio.sleep(self.reconnect_delay)

    async def stop(self):
        """
        Остановка WebSocket клиента
        """
        logger.info("Stopping PumpPortal WebSocket client...")
        self._running = False
        await self.disconnect()

    @property
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения
        """
        return self._websocket is not None and not self._websocket.closed

    @property
    def status(self) -> Dict[str, Any]:
        """
        Статус клиента для мониторинга
        """
        return {
            "connected": self.is_connected,
            "running": self._running,
            "reconnect_count": self._reconnect_count,
            "subscriptions": len(self._subscriptions),
            "websocket_url": self.websocket_url
        }


class PumpPortalManager:
    """
    Менеджер для управления PumpPortal WebSocket клиентом
    с интеграцией в систему токенов
    """
    
    def __init__(self):
        self.client: Optional[PumpPortalWebSocketClient] = None
        self._running = False
        
        # Статистика событий
        self.stats = {
            "migrations_received": 0,
            "new_tokens_received": 0,
            "tokens_created": 0,
            "errors": 0,
            "started_at": None
        }

    async def start(self):
        """
        Запуск менеджера PumpPortal
        """
        if self._running:
            logger.warning("PumpPortal manager already running")
            return
            
        logger.info("🚀 Starting PumpPortal manager...")
        self._running = True
        self.stats["started_at"] = datetime.now()
        
        # Создаем клиент с обработчиками
        self.client = PumpPortalWebSocketClient(
            on_migration=self._handle_migration_event,
            on_new_token=self._handle_new_token_event,
            on_error=self._handle_error
        )
        
        try:
            # Запускаем клиент (подписываемся только на миграции по умолчанию)
            await self.client.start(
                subscribe_migrations=True,
                subscribe_new_tokens=False  # Можно включить позже если нужно
            )
            
        except Exception as e:
            logger.error(f"Error starting PumpPortal manager: {e}")
            self.stats["errors"] += 1
            
        finally:
            self._running = False
            logger.info("PumpPortal manager stopped")

    async def stop(self):
        """
        Остановка менеджера
        """
        logger.info("Stopping PumpPortal manager...")
        self._running = False
        
        if self.client:
            await self.client.stop()
            self.client = None

    async def _handle_migration_event(self, event: TokenMigrationEvent):
        """
        Обработка события миграции токена
        """
        try:
            logger.info(
                f"🎯 Token migration detected: {event.token_address[:8]}...",
                extra={
                    "token_address": event.token_address,
                    "liquidity_pool": event.liquidity_pool_address,
                    "dex_name": event.dex_name,
                    "event_type": "migration"
                }
            )
            
            self.stats["migrations_received"] += 1
            
            # Создаем токен в базе данных
            success = await self._create_token_from_migration(event)
            if success:
                self.stats["tokens_created"] += 1
                
        except Exception as e:
            logger.error(f"Error handling migration event: {e}")
            self.stats["errors"] += 1

    async def _handle_new_token_event(self, event: NewTokenEvent):
        """
        Обработка события создания нового токена
        """
        try:
            logger.info(
                f"🆕 New token detected: {event.token_address[:8]}... ({event.symbol})",
                extra={
                    "token_address": event.token_address,
                    "name": event.name,
                    "symbol": event.symbol,
                    "event_type": "new_token"
                }
            )
            
            self.stats["new_tokens_received"] += 1
            
            # TODO: Решить, создавать ли токены сразу при создании 
            # или только при миграции (согласно vision.md)
            
        except Exception as e:
            logger.error(f"Error handling new token event: {e}")
            self.stats["errors"] += 1

    def _handle_error(self, error: Exception):
        """
        Обработка ошибок WebSocket
        """
        logger.error(f"PumpPortal WebSocket error: {error}")
        self.stats["errors"] += 1

    async def _create_token_from_migration(self, event: TokenMigrationEvent) -> bool:
        """
        Создание токена в базе данных на основе события миграции
        """
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from app.database import SessionLocal
            from app.crud import token_crud
            from app.schemas.token import TokenCreate
            
            if not SessionLocal:
                logger.error("Database not configured")
                return False
            
            # Создаем сессию БД
            db = SessionLocal()
            
            try:
                # Проверяем, не существует ли уже такой токен
                existing_token = token_crud.get_by_address(
                    db, 
                    token_address=event.token_address
                )
                
                if existing_token:
                    logger.info(f"Token {event.token_address[:8]}... already exists, skipping")
                    return True
                
                # Создаем новый токен
                token_create = TokenCreate(token_address=event.token_address)
                created_token = token_crud.create_with_history(db, obj_in=token_create)
                
                logger.info(
                    f"✅ Token created: {created_token.token_address[:8]}... (ID: {str(created_token.id)[:8]}...)",
                    extra={
                        "token_id": str(created_token.id),
                        "token_address": created_token.token_address,
                        "status": created_token.status.value,
                        "operation": "token_created_from_migration"
                    }
                )
                
                # TODO: Если есть данные о пуле, создаем и его
                if event.liquidity_pool_address and event.dex_name:
                    await self._create_pool_from_migration(db, created_token.id, event)
                
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to create token from migration: {e}")
            return False

    async def _create_pool_from_migration(self, db, token_id: str, event: TokenMigrationEvent):
        """
        Создание пула на основе данных миграции
        """
        try:
            from app.crud import pool_crud
            from app.schemas.pool import PoolCreate
            
            pool_create = PoolCreate(
                pool_address=event.liquidity_pool_address,
                token_id=str(token_id),
                dex_name=event.dex_name or "raydium",
                is_active=True
            )
            
            created_pool = pool_crud.create(db, obj_in=pool_create)
            
            logger.info(
                f"✅ Pool created: {created_pool.pool_address[:8]}... ({created_pool.dex_name})",
                extra={
                    "pool_id": str(created_pool.id),
                    "pool_address": created_pool.pool_address,
                    "token_id": str(token_id),
                    "dex_name": created_pool.dex_name,
                    "operation": "pool_created_from_migration"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create pool from migration: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику работы
        """
        stats = self.stats.copy()
        
        if self.client:
            stats.update(self.client.status)
            
        if stats["started_at"]:
            uptime = datetime.now() - stats["started_at"]
            stats["uptime_seconds"] = uptime.total_seconds()
            
        return stats


# Глобальный экземпляр менеджера
pumpportal_manager = PumpPortalManager()
