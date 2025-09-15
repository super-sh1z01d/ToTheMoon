"""
Birdeye API client for token metrics
Интеграция с https://public-api.birdeye.so
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from decimal import Decimal

import aiohttp
import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class TokenOverview:
    """
    Обзорные данные токена от Birdeye
    """
    address: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    liquidity: Optional[float] = None
    holders: Optional[int] = None
    decimals: Optional[int] = None
    supply: Optional[float] = None
    
    @classmethod
    def from_api_response(cls, address: str, data: Dict[str, Any]) -> 'TokenOverview':
        """Создание объекта из ответа Birdeye API"""
        return cls(
            address=address,
            name=data.get('name'),
            symbol=data.get('symbol'),
            price=data.get('price'),
            market_cap=data.get('mc'),
            volume_24h=data.get('v24hUSD'),
            liquidity=data.get('liquidity'),
            holders=data.get('holder', data.get('holders')),
            decimals=data.get('decimals'),
            supply=data.get('supply')
        )


@dataclass 
class TokenTrades:
    """
    Данные торгов токена от Birdeye
    """
    address: str
    trades_5m: int = 0
    trades_1h: int = 0
    volume_5m: Decimal = Decimal('0')
    volume_1h: Decimal = Decimal('0')
    buys_volume_5m: Decimal = Decimal('0')
    sells_volume_5m: Decimal = Decimal('0')
    
    @classmethod
    def from_api_response(cls, address: str, data: Dict[str, Any]) -> 'TokenTrades':
        """Создание объекта из ответа Birdeye API"""
        items = data.get('data', {}).get('items', [])
        
        # Агрегируем данные по временным интервалам
        trades_5m = 0
        trades_1h = 0
        volume_5m = Decimal('0')
        volume_1h = Decimal('0')
        buys_5m = Decimal('0')
        sells_5m = Decimal('0')
        
        now = datetime.now()
        cutoff_5m = now - timedelta(minutes=5)
        cutoff_1h = now - timedelta(hours=1)
        
        for trade in items:
            trade_time = datetime.fromtimestamp(trade.get('blockUnixTime', 0))
            volume_usd = Decimal(str(trade.get('volumeInUSD', 0)))
            
            if trade_time >= cutoff_5m:
                trades_5m += 1
                volume_5m += volume_usd
                
                # Разделяем покупки и продажи
                if trade.get('txType') == 'buy':
                    buys_5m += volume_usd
                else:
                    sells_5m += volume_usd
                    
            if trade_time >= cutoff_1h:
                trades_1h += 1
                volume_1h += volume_usd
        
        return cls(
            address=address,
            trades_5m=trades_5m,
            trades_1h=trades_1h,
            volume_5m=volume_5m,
            volume_1h=volume_1h,
            buys_volume_5m=buys_5m,
            sells_volume_5m=sells_5m
        )


class BirdeyeRateLimitError(Exception):
    """Ошибка превышения rate limit"""
    pass


class BirdeyeAPIError(Exception):
    """Общая ошибка Birdeye API"""
    pass


class BirdeyeClient:
    """
    HTTP клиент для работы с Birdeye API
    
    Поддерживает:
    - Token overview (базовые данные)
    - Token trades (история торгов) 
    - Redis кеширование
    - Rate limit handling
    - Error recovery
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        redis_client: Optional[redis.Redis] = None,
        cache_ttl: int = 60,
        rate_limit_delay: float = 0.2
    ):
        self.api_key = api_key or os.getenv("BIRDEYE_API_KEY")
        self.base_url = base_url or os.getenv("BIRDEYE_BASE_URL", "https://public-api.birdeye.so")
        self.cache_ttl = cache_ttl
        self.rate_limit_delay = rate_limit_delay
        
        # Redis для кеширования
        self.redis_client = redis_client
        
        # Статистика использования
        self.stats = {
            "requests_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limits": 0,
            "errors": 0,
            "last_request": None
        }
        
        # HTTP сессия
        self._session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Birdeye API key not configured")
        else:
            logger.info(f"Birdeye client initialized with API key: {self.api_key[:10]}...")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение HTTP сессии"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            headers = {
                "X-API-KEY": self.api_key,
                "Accept": "application/json",
                "User-Agent": "ToTheMoon2/1.0"
            }
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
            
        return self._session

    async def close(self):
        """Закрытие HTTP сессии"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_cache_key(self, endpoint: str, token_address: str) -> str:
        """Генерация ключа для Redis кеша"""
        return f"birdeye:{endpoint}:{token_address}"

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получение данных из кеша"""
        if not self.redis_client:
            return None
            
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                self.stats["cache_hits"] += 1
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            
        return None

    async def _set_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Сохранение данных в кеш"""
        if not self.redis_client:
            return
            
        try:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def _make_request(
        self, 
        endpoint: str, 
        token_address: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выполнение HTTP запроса к Birdeye API
        """
        # Проверяем кеш
        cache_key = self._get_cache_key(endpoint, token_address)
        cached_data = await self._get_from_cache(cache_key)
        
        if cached_data:
            logger.debug(f"Cache hit for {endpoint}:{token_address}")
            return cached_data
        
        self.stats["cache_misses"] += 1
        
        # Rate limiting - простая задержка между запросами
        if self.stats["last_request"]:
            time_since_last = datetime.now() - self.stats["last_request"]
            if time_since_last.total_seconds() < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay)
        
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            # Добавляем token_address в параметры если нужно
            if params is None:
                params = {}
            
            logger.debug(f"Making request to {url}")
            
            async with session.get(url, params=params) as response:
                self.stats["requests_made"] += 1
                self.stats["last_request"] = datetime.now()
                
                if response.status == 429:
                    # Rate limit exceeded
                    self.stats["rate_limits"] += 1
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit hit, waiting {retry_after}s")
                    
                    await asyncio.sleep(retry_after)
                    raise BirdeyeRateLimitError(f"Rate limit exceeded, retry after {retry_after}s")
                
                if response.status == 401:
                    raise BirdeyeAPIError("Invalid API key")
                
                if response.status == 404:
                    logger.warning(f"Token {token_address} not found in Birdeye")
                    return {"error": "token_not_found"}
                
                if not response.ok:
                    error_text = await response.text()
                    raise BirdeyeAPIError(f"HTTP {response.status}: {error_text}")
                
                data = await response.json()
                
                # Сохраняем в кеш успешные ответы
                if data and "error" not in data:
                    await self._set_to_cache(cache_key, data)
                
                return data
                
        except aiohttp.ClientError as e:
            self.stats["errors"] += 1
            logger.error(f"HTTP client error: {e}")
            raise BirdeyeAPIError(f"Network error: {e}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Unexpected error in Birdeye request: {e}")
            raise

    async def get_token_overview(self, token_address: str) -> Optional[TokenOverview]:
        """
        Получение обзорных данных токена
        """
        try:
            data = await self._make_request(
                f"defi/token_overview",
                token_address,
                params={"address": token_address}
            )
            
            if "error" in data:
                logger.warning(f"Token overview error for {token_address}: {data['error']}")
                return None
                
            return TokenOverview.from_api_response(token_address, data.get('data', {}))
            
        except BirdeyeRateLimitError:
            logger.warning(f"Rate limited for token overview {token_address}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get token overview for {token_address}: {e}")
            return None

    async def get_token_trades(
        self, 
        token_address: str, 
        limit: int = 1000,
        offset: int = 0
    ) -> Optional[TokenTrades]:
        """
        Получение данных торгов токена
        """
        try:
            data = await self._make_request(
                f"defi/txs/token",
                token_address,
                params={
                    "address": token_address,
                    "limit": limit,
                    "offset": offset,
                    "sort_type": "desc"
                }
            )
            
            if "error" in data:
                logger.warning(f"Token trades error for {token_address}: {data['error']}")
                return None
                
            return TokenTrades.from_api_response(token_address, data)
            
        except BirdeyeRateLimitError:
            logger.warning(f"Rate limited for token trades {token_address}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get token trades for {token_address}: {e}")
            return None

    async def get_token_security(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Получение данных безопасности токена
        """
        try:
            data = await self._make_request(
                f"defi/token_security",
                token_address,
                params={"address": token_address}
            )
            
            if "error" in data:
                logger.warning(f"Token security error for {token_address}: {data['error']}")
                return None
                
            return data.get('data', {})
            
        except BirdeyeRateLimitError:
            logger.warning(f"Rate limited for token security {token_address}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get token security for {token_address}: {e}")
            return None

    async def store_raw_data(
        self, 
        token_address: str, 
        endpoint: str, 
        response_data: Dict[str, Any]
    ):
        """
        Сохранение raw данных в БД для восстановления
        """
        try:
            from app.database import SessionLocal
            from app.models.raw_data import BirdeyeRawData
            
            if not SessionLocal:
                return
                
            db = SessionLocal()
            
            try:
                # Создаем запись с TTL
                raw_data = BirdeyeRawData.create_with_ttl(
                    token_address=token_address,
                    endpoint=endpoint,
                    response_data=response_data,
                    ttl_days=7
                )
                
                db.add(raw_data)
                db.commit()
                
                logger.debug(f"Stored raw data for {token_address}:{endpoint}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to store raw data: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику использования API
        """
        stats = self.stats.copy()
        
        # Добавляем информацию о конфигурации
        stats.update({
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "cache_ttl": self.cache_ttl,
            "redis_configured": self.redis_client is not None,
            "cache_hit_rate": (
                self.stats["cache_hits"] / 
                (self.stats["cache_hits"] + self.stats["cache_misses"])
                if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0 
                else 0
            )
        })
        
        return stats


class BirdeyeManager:
    """
    Менеджер для управления Birdeye API клиентом
    с интеграцией в систему метрик
    """
    
    def __init__(self):
        self.client: Optional[BirdeyeClient] = None
        self._redis_client: Optional[redis.Redis] = None
        
    async def initialize(self):
        """
        Инициализация менеджера
        """
        try:
            # Подключение к Redis для кеширования
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Проверка подключения
            await self._redis_client.ping()
            logger.info("✅ Redis connection for Birdeye cache established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self._redis_client = None
        
        # Создание Birdeye клиента
        cache_ttl = int(os.getenv("BIRDEYE_CACHE_TTL_SECONDS", "60"))
        
        self.client = BirdeyeClient(
            redis_client=self._redis_client,
            cache_ttl=cache_ttl
        )
        
        logger.info("✅ Birdeye manager initialized")

    async def close(self):
        """
        Закрытие соединений
        """
        if self.client:
            await self.client.close()
            
        if self._redis_client:
            await self._redis_client.close()
            
        logger.info("Birdeye manager closed")

    async def fetch_token_metrics(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Получение полных метрик токена с агрегацией данных
        """
        if not self.client:
            logger.error("Birdeye client not initialized")
            return None
            
        try:
            # Параллельно получаем обзор и торги
            overview_task = self.client.get_token_overview(token_address)
            trades_task = self.client.get_token_trades(token_address)
            
            overview, trades = await asyncio.gather(
                overview_task, 
                trades_task,
                return_exceptions=True
            )
            
            # Обрабатываем результаты
            if isinstance(overview, Exception):
                logger.error(f"Overview error: {overview}")
                overview = None
                
            if isinstance(trades, Exception):
                logger.error(f"Trades error: {trades}")
                trades = None
            
            # Если ничего не получили, возвращаем None
            if not overview and not trades:
                return None
            
            # Агрегируем данные
            metrics = {
                "token_address": token_address,
                "timestamp": datetime.now().isoformat(),
                
                # Основные данные
                "name": overview.name if overview else None,
                "symbol": overview.symbol if overview else None,
                "price": overview.price if overview else None,
                "market_cap": overview.market_cap if overview else None,
                "liquidity_usd": overview.liquidity if overview else 0,
                "holders_count": overview.holders if overview else 0,
                
                # Торговые данные
                "tx_count_5m": trades.trades_5m if trades else 0,
                "tx_count_1h": trades.trades_1h if trades else 0,
                "volume_5m_usd": float(trades.volume_5m) if trades else 0,
                "volume_1h_usd": float(trades.volume_1h) if trades else 0,
                "buys_volume_5m_usd": float(trades.buys_volume_5m) if trades else 0,
                "sells_volume_5m_usd": float(trades.sells_volume_5m) if trades else 0,
            }
            
            logger.info(
                f"✅ Fetched metrics for {token_address[:8]}...",
                extra={
                    "token_address": token_address,
                    "tx_5m": metrics["tx_count_5m"],
                    "volume_5m": metrics["volume_5m_usd"],
                    "holders": metrics["holders_count"]
                }
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to fetch token metrics for {token_address}: {e}")
            return None

    async def save_token_metrics(self, token_address: str) -> bool:
        """
        Получение и сохранение метрик токена в БД
        """
        try:
            # Получаем метрики
            metrics_data = await self.fetch_token_metrics(token_address)
            if not metrics_data:
                return False
            
            # Сохраняем в БД
            from app.database import SessionLocal
            from app.models.metrics import TokenMetrics
            from app.crud import token_crud
            
            if not SessionLocal:
                logger.error("Database not configured")
                return False
            
            db = SessionLocal()
            
            try:
                # Находим токен
                token = token_crud.get_by_address(db, token_address=token_address)
                if not token:
                    logger.warning(f"Token {token_address} not found in database")
                    return False
                
                # Создаем запись метрик
                token_metrics = TokenMetrics(
                    token_id=token.id,
                    timestamp=datetime.now(),
                    tx_count_5m=metrics_data["tx_count_5m"],
                    tx_count_1h=metrics_data["tx_count_1h"],
                    volume_5m_usd=Decimal(str(metrics_data["volume_5m_usd"])),
                    volume_1h_usd=Decimal(str(metrics_data["volume_1h_usd"])),
                    buys_volume_5m_usd=Decimal(str(metrics_data["buys_volume_5m_usd"])),
                    sells_volume_5m_usd=Decimal(str(metrics_data["sells_volume_5m_usd"])),
                    holders_count=metrics_data["holders_count"],
                    liquidity_usd=Decimal(str(metrics_data["liquidity_usd"]))
                )
                
                db.add(token_metrics)
                db.commit()
                
                logger.info(
                    f"✅ Metrics saved for {token_address[:8]}...",
                    extra={
                        "token_id": str(token.id),
                        "token_address": token_address,
                        "metrics_id": str(token_metrics.id)
                    }
                )
                
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to save token metrics for {token_address}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику работы
        """
        stats = {
            "client_initialized": self.client is not None,
            "redis_connected": self._redis_client is not None
        }
        
        if self.client:
            stats.update(self.client.get_stats())
            
        return stats


# Глобальный экземпляр менеджера
birdeye_manager = BirdeyeManager()
