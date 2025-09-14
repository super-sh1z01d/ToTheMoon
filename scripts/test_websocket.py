#!/usr/bin/env python3
"""
Test WebSocket integration with PumpPortal
Простое тестирование WebSocket подключения
"""

import asyncio
import sys
import signal
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.data_sources.pumpportal_websocket import (
    PumpPortalWebSocketClient,
    TokenMigrationEvent,
    NewTokenEvent
)


class WebSocketTester:
    """
    Тестер для WebSocket интеграции
    """
    
    def __init__(self):
        self.client: PumpPortalWebSocketClient = None
        self.running = False
        self.events_received = 0
        
    def handle_migration(self, event: TokenMigrationEvent):
        """Обработчик миграций для тестирования"""
        self.events_received += 1
        print(f"🎯 MIGRATION #{self.events_received}:")
        print(f"   Token: {event.token_address}")
        print(f"   Pool: {event.liquidity_pool_address}")
        print(f"   DEX: {event.dex_name}")
        print(f"   Time: {event.timestamp}")
        print("-" * 50)
        
    def handle_new_token(self, event: NewTokenEvent):
        """Обработчик новых токенов для тестирования"""
        self.events_received += 1
        print(f"🆕 NEW TOKEN #{self.events_received}:")
        print(f"   Token: {event.token_address}")
        print(f"   Name: {event.name}")
        print(f"   Symbol: {event.symbol}")
        print(f"   Time: {event.timestamp}")
        print("-" * 50)
        
    def handle_error(self, error: Exception):
        """Обработчик ошибок для тестирования"""
        print(f"❌ ERROR: {error}")
        
    async def run_test(self, test_duration: int = 60):
        """
        Запуск теста WebSocket подключения
        
        Args:
            test_duration: Длительность теста в секундах
        """
        print(f"🧪 ТЕСТ WEBSOCKET ИНТЕГРАЦИИ")
        print("=" * 50)
        print(f"Длительность теста: {test_duration} секунд")
        print("Для остановки используйте Ctrl+C")
        print("=" * 50)
        
        # Создаем клиент
        self.client = PumpPortalWebSocketClient(
            on_migration=self.handle_migration,
            on_new_token=self.handle_new_token,
            on_error=self.handle_error
        )
        
        self.running = True
        
        try:
            # Подключаемся
            connected = await self.client.connect()
            if not connected:
                print("❌ Не удалось подключиться к WebSocket")
                return False
            
            print("✅ Подключение установлено")
            
            # Подписываемся на события
            migration_ok = await self.client.subscribe_migrations()
            new_token_ok = await self.client.subscribe_new_tokens()
            
            if not migration_ok:
                print("❌ Не удалось подписаться на миграции")
            else:
                print("✅ Подписка на миграции активна")
                
            if not new_token_ok:
                print("❌ Не удалось подписаться на новые токены")
            else:
                print("✅ Подписка на новые токены активна")
            
            if not migration_ok and not new_token_ok:
                print("❌ Не удалось настроить подписки")
                return False
            
            print(f"\n🎧 Прослушивание событий... (до {test_duration}s)")
            print("Ожидаем события от PumpPortal...")
            
            # Ждем события или таймаут
            try:
                await asyncio.wait_for(
                    self.client._listen_loop(),
                    timeout=test_duration
                )
            except asyncio.TimeoutError:
                print(f"\n⏰ Тест завершен по таймауту ({test_duration}s)")
            
            return True
            
        except KeyboardInterrupt:
            print("\n🛑 Тест остановлен пользователем")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка теста: {e}")
            return False
            
        finally:
            self.running = False
            if self.client:
                await self.client.disconnect()
            
            print("\n" + "=" * 50)
            print(f"📊 СТАТИСТИКА ТЕСТА:")
            print(f"   Получено событий: {self.events_received}")
            print(f"   Статус подключения: {'✅' if self.client and self.client.is_connected else '❌'}")
            
            if self.events_received > 0:
                print("🎉 Интеграция работает!")
            else:
                print("⚠️  События не получены (возможно, низкая активность)")

async def simple_connection_test():
    """
    Простой тест подключения без ожидания событий
    """
    print("🔍 ПРОСТОЙ ТЕСТ ПОДКЛЮЧЕНИЯ")
    print("=" * 40)
    
    client = PumpPortalWebSocketClient()
    
    try:
        connected = await client.connect()
        if connected:
            print("✅ Подключение к PumpPortal успешно")
            
            # Тест подписки
            migration_ok = await client.subscribe_migrations()
            print(f"Подписка на миграции: {'✅' if migration_ok else '❌'}")
            
            await client.disconnect()
            return True
        else:
            print("❌ Не удалось подключиться к PumpPortal")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test PumpPortal WebSocket integration")
    parser.add_argument(
        "--mode", 
        choices=["simple", "listen"], 
        default="simple",
        help="Test mode: simple (connection test) or listen (wait for events)"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=60,
        help="Test duration in seconds for listen mode"
    )
    
    args = parser.parse_args()
    
    # Обработка Ctrl+C
    def signal_handler(sig, frame):
        print("\n🛑 Получен сигнал остановки")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Запуск теста
    if args.mode == "simple":
        success = asyncio.run(simple_connection_test())
    else:
        tester = WebSocketTester()
        success = asyncio.run(tester.run_test(args.duration))
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
