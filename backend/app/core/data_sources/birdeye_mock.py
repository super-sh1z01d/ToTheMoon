"""
Mock Birdeye client for development and testing
Заглушка для разработки при недоступности реального API
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal

from app.core.data_sources.birdeye_client import (
    TokenOverview, TokenTrades, BirdeyeClient, BirdeyeManager
)

logger = logging.getLogger(__name__)


class MockBirdeyeClient(BirdeyeClient):
    """
    Mock версия Birdeye клиента для тестирования
    """
    
    def __init__(self, **kwargs):
        # Не вызываем super().__init__ чтобы избежать зависимостей
        self.api_key = "mock_key"
        self.base_url = "mock://birdeye.api"
        self.cache_ttl = 60
        self.rate_limit_delay = 0.1
        
        self.stats = {
            "requests_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limits": 0,
            "errors": 0,
            "last_request": None
        }
        
        logger.info("MockBirdeyeClient initialized")

    async def _get_session(self):
        """Mock session"""
        return None

    async def close(self):
        """Mock close"""
        pass

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Mock cache (всегда miss)"""
        return None

    async def _set_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Mock cache set"""
        pass

    def _generate_mock_overview_data(self, token_address: str) -> Dict[str, Any]:
        """Генерация mock данных для token overview"""
        # Генерируем псевдо-случайные, но детерминированные данные
        random.seed(hash(token_address) % 1000000)
        
        return {
            "address": token_address,
            "name": f"Mock Token {token_address[:8]}",
            "symbol": f"MCK{token_address[2:5].upper()}",
            "decimals": 6,
            "price": round(random.uniform(0.001, 100), 6),
            "mc": round(random.uniform(10000, 10000000), 2),
            "v24hUSD": round(random.uniform(1000, 1000000), 2),
            "liquidity": round(random.uniform(5000, 500000), 2),
            "holder": random.randint(100, 10000),
            "supply": round(random.uniform(1000000, 1000000000), 2)
        }

    def _generate_mock_trades_data(self, token_address: str) -> Dict[str, Any]:
        """Генерация mock данных для trades"""
        random.seed(hash(token_address) % 1000000)
        
        # Генерируем mock торги за последние часы
        now = datetime.now()
        trades = []
        
        # Создаем 50-200 торгов за последний час
        num_trades = random.randint(50, 200)
        
        for i in range(num_trades):
            # Время торга в последний час
            trade_time = now - timedelta(
                seconds=random.randint(0, 3600)
            )
            
            trades.append({
                "blockUnixTime": int(trade_time.timestamp()),
                "txType": random.choice(["buy", "sell"]),
                "volumeInUSD": round(random.uniform(10, 10000), 2),
                "priceInUSD": round(random.uniform(0.001, 100), 6)
            })
        
        return {
            "data": {
                "items": trades
            }
        }

    async def get_token_overview(self, token_address: str) -> Optional[TokenOverview]:
        """Mock получение overview"""
        try:
            # Имитируем задержку API
            await asyncio.sleep(0.1)
            
            self.stats["requests_made"] += 1
            self.stats["cache_misses"] += 1
            self.stats["last_request"] = datetime.now()
            
            # Генерируем mock данные
            mock_data = self._generate_mock_overview_data(token_address)
            
            logger.debug(f"Mock overview for {token_address[:8]}...")
            return TokenOverview.from_api_response(token_address, mock_data)
            
        except Exception as e:
            logger.error(f"Mock overview error: {e}")
            self.stats["errors"] += 1
            return None

    async def get_token_trades(
        self, 
        token_address: str, 
        limit: int = 1000,
        offset: int = 0
    ) -> Optional[TokenTrades]:
        """Mock получение trades"""
        try:
            # Имитируем задержку API
            await asyncio.sleep(0.1)
            
            self.stats["requests_made"] += 1
            self.stats["cache_misses"] += 1
            self.stats["last_request"] = datetime.now()
            
            # Генерируем mock данные
            mock_data = self._generate_mock_trades_data(token_address)
            
            logger.debug(f"Mock trades for {token_address[:8]}...")
            return TokenTrades.from_api_response(token_address, mock_data)
            
        except Exception as e:
            logger.error(f"Mock trades error: {e}")
            self.stats["errors"] += 1
            return None

    async def get_token_security(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Mock получение security данных"""
        try:
            await asyncio.sleep(0.1)
            
            self.stats["requests_made"] += 1
            
            # Mock security данные
            return {
                "isLocked": True,
                "isMutable": False,
                "isVerified": random.choice([True, False]),
                "hasFreeze": False,
                "hasMint": False
            }
            
        except Exception as e:
            logger.error(f"Mock security error: {e}")
            return None


class MockBirdeyeManager(BirdeyeManager):
    """
    Mock версия менеджера для тестирования
    """
    
    async def initialize(self):
        """Mock инициализация"""
        # Создаем mock клиент
        self.client = MockBirdeyeClient()
        logger.info("✅ Mock Birdeye manager initialized")

    async def close(self):
        """Mock закрытие"""
        if self.client:
            await self.client.close()
        logger.info("Mock Birdeye manager closed")


# Функция для переключения на mock режим
def use_mock_birdeye():
    """
    Переключение на mock версию Birdeye API
    """
    global birdeye_manager
    
    from app.core.data_sources import birdeye_client
    
    # Заменяем глобальный менеджер на mock версию
    birdeye_client.birdeye_manager = MockBirdeyeManager()
    
    logger.info("🎭 Switched to Mock Birdeye API")
    return birdeye_client.birdeye_manager
