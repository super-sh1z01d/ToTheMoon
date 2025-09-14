#!/usr/bin/env python3
"""
Test Birdeye API integration
Простое тестирование Birdeye API подключения
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.data_sources.birdeye_client import BirdeyeClient, birdeye_manager


class BirdeyeTester:
    """
    Тестер для Birdeye API интеграции
    """
    
    def __init__(self):
        self.client: BirdeyeClient = None
        
    async def test_connection(self) -> bool:
        """Тест подключения к API"""
        print("🔍 ТЕСТ ПОДКЛЮЧЕНИЯ К BIRDEYE API")
        print("=" * 50)
        
        # Проверяем API key
        api_key = os.getenv("BIRDEYE_API_KEY", "b2b52f3bd99c48e9b24c26ae0987cbe9")
        if not api_key:
            print("❌ BIRDEYE_API_KEY не установлен")
            return False
        
        print(f"API Key: {api_key[:10]}...")
        
        try:
            # Создаем клиент
            self.client = BirdeyeClient(api_key=api_key)
            
            # Тестируем с SOL токеном
            test_token = "So11111111111111111111111111111111111111112"
            print(f"Тестовый токен: {test_token[:8]}... (SOL)")
            
            # Тест overview
            print("\n🔍 Тестирование token overview...")
            overview = await self.client.get_token_overview(test_token)
            
            if overview:
                print("✅ Token overview получен:")
                print(f"   Name: {overview.name}")
                print(f"   Symbol: {overview.symbol}")
                print(f"   Price: ${overview.price}")
                print(f"   Liquidity: ${overview.liquidity}")
                print(f"   Holders: {overview.holders}")
            else:
                print("❌ Token overview не получен")
                return False
            
            # Тест trades
            print("\n🔍 Тестирование token trades...")
            trades = await self.client.get_token_trades(test_token, limit=100)
            
            if trades:
                print("✅ Token trades получены:")
                print(f"   Trades 5m: {trades.trades_5m}")
                print(f"   Trades 1h: {trades.trades_1h}")
                print(f"   Volume 5m: ${trades.volume_5m}")
                print(f"   Volume 1h: ${trades.volume_1h}")
                print(f"   Buys 5m: ${trades.buys_volume_5m}")
                print(f"   Sells 5m: ${trades.sells_volume_5m}")
            else:
                print("⚠️  Token trades не получены (возможно, нет активности)")
            
            # Тест агрегированных метрик
            print("\n🔍 Тестирование агрегированных метрик...")
            metrics = await self.client.fetch_token_metrics(test_token)
            
            if metrics:
                print("✅ Агрегированные метрики получены:")
                print(f"   TX 5m: {metrics['tx_count_5m']}")
                print(f"   TX 1h: {metrics['tx_count_1h']}")
                print(f"   Volume 5m: ${metrics['volume_5m_usd']}")
                print(f"   Holders: {metrics['holders_count']}")
                print(f"   Liquidity: ${metrics['liquidity_usd']}")
            else:
                print("❌ Агрегированные метрики не получены")
                return False
            
            print("\n✅ Все тесты пройдены успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False
            
        finally:
            if self.client:
                await self.client.close()

    async def test_manager(self) -> bool:
        """Тест менеджера с Redis кешированием"""
        print("\n🔍 ТЕСТ BIRDEYE МЕНЕДЖЕРА")
        print("=" * 40)
        
        try:
            # Инициализируем менеджер
            await birdeye_manager.initialize()
            
            if not birdeye_manager.client:
                print("❌ Менеджер не инициализирован")
                return False
            
            print("✅ Менеджер инициализирован")
            
            # Тест получения метрик
            test_token = "So11111111111111111111111111111111111111112"
            
            print(f"Получаем метрики для {test_token[:8]}...")
            
            # Первый запрос (должен попасть в API)
            metrics1 = await birdeye_manager.fetch_token_metrics(test_token)
            
            if metrics1:
                print("✅ Первый запрос успешен (из API)")
            else:
                print("❌ Первый запрос не удался")
                return False
            
            # Второй запрос (должен попасть в кеш)
            metrics2 = await birdeye_manager.fetch_token_metrics(test_token)
            
            if metrics2:
                print("✅ Второй запрос успешен (из кеша)")
            else:
                print("❌ Второй запрос не удался")
                return False
            
            # Проверяем статистику
            stats = birdeye_manager.get_stats()
            print(f"\n📊 Статистика API:")
            print(f"   Запросы: {stats.get('requests_made', 0)}")
            print(f"   Cache hits: {stats.get('cache_hits', 0)}")
            print(f"   Cache misses: {stats.get('cache_misses', 0)}")
            print(f"   Cache hit rate: {stats.get('cache_hit_rate', 0):.2%}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования менеджера: {e}")
            return False
            
        finally:
            await birdeye_manager.close()

    async def test_database_integration(self) -> bool:
        """Тест сохранения данных в БД"""
        print("\n🔍 ТЕСТ ИНТЕГРАЦИИ С БД")
        print("=" * 35)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест БД")
            return True
        
        try:
            # Инициализируем менеджер
            await birdeye_manager.initialize()
            
            # Тест сохранения метрик
            test_token = "So11111111111111111111111111111111111111112"
            
            print(f"Сохраняем метрики для {test_token[:8]}...")
            
            success = await birdeye_manager.save_token_metrics(test_token)
            
            if success:
                print("✅ Метрики сохранены в БД")
            else:
                print("❌ Не удалось сохранить метрики")
                return False
            
            # Проверяем CRUD операции
            from app.database import SessionLocal
            from app.crud import token_crud, token_metrics_crud
            
            if SessionLocal:
                db = SessionLocal()
                try:
                    # Ищем токен
                    token = token_crud.get_by_address(db, token_address=test_token)
                    if token:
                        print(f"✅ Токен найден в БД: {token.token_address[:8]}...")
                        
                        # Ищем метрики
                        metrics = token_metrics_crud.get_latest(db, token_id=token.id)
                        if metrics:
                            print(f"✅ Метрики найдены: TX 5m={metrics.tx_count_5m}")
                        else:
                            print("⚠️  Метрики не найдены в БД")
                    else:
                        print(f"⚠️  Токен {test_token} не найден в БД")
                        print("   Создайте токен сначала или запустите WebSocket интеграцию")
                        
                finally:
                    db.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка интеграции с БД: {e}")
            return False
            
        finally:
            await birdeye_manager.close()


async def quick_api_test():
    """
    Быстрый тест API без менеджера
    """
    print("🔍 БЫСТРЫЙ ТЕСТ BIRDEYE API")
    print("=" * 40)
    
    api_key = os.getenv("BIRDEYE_API_KEY", "b2b52f3bd99c48e9b24c26ae0987cbe9")
    
    if not api_key:
        print("❌ API ключ не найден")
        return False
    
    client = BirdeyeClient(api_key=api_key)
    
    try:
        # Тест с SOL
        test_token = "So11111111111111111111111111111111111111112"
        print(f"Тестируем получение данных для SOL: {test_token[:8]}...")
        
        overview = await client.get_token_overview(test_token)
        
        if overview:
            print(f"✅ Успешно! SOL price: ${overview.price}")
            print(f"   Market cap: ${overview.market_cap}")
            print(f"   Liquidity: ${overview.liquidity}")
            return True
        else:
            print("❌ Не удалось получить данные")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
        
    finally:
        await client.close()


def main():
    """
    Главная функция тестирования
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Birdeye API integration")
    parser.add_argument(
        "--mode", 
        choices=["quick", "full", "manager", "db"], 
        default="quick",
        help="Test mode"
    )
    
    args = parser.parse_args()
    
    # Устанавливаем API ключ если не задан
    if not os.getenv("BIRDEYE_API_KEY"):
        os.environ["BIRDEYE_API_KEY"] = "b2b52f3bd99c48e9b24c26ae0987cbe9"
    
    # Запуск тестов
    if args.mode == "quick":
        success = asyncio.run(quick_api_test())
    elif args.mode == "full":
        tester = BirdeyeTester()
        success = asyncio.run(tester.test_connection())
    elif args.mode == "manager":
        tester = BirdeyeTester()
        success = asyncio.run(tester.test_manager())
    elif args.mode == "db":
        tester = BirdeyeTester()
        success = asyncio.run(tester.test_database_integration())
    
    if success:
        print("\n🎉 Тестирование Birdeye API завершено успешно!")
    else:
        print("\n❌ Тестирование Birdeye API не удалось")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
