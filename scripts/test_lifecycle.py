#!/usr/bin/env python3
"""
Test Token Lifecycle Management
Тестирование системы управления жизненным циклом токенов
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class LifecycleTester:
    """
    Тестер для lifecycle системы
    """
    
    def __init__(self):
        self.manager = None
        
    async def test_lifecycle_manager(self) -> bool:
        """Тест lifecycle менеджера"""
        print("🔍 ТЕСТ LIFECYCLE MANAGER")
        print("=" * 40)
        
        try:
            from app.core.lifecycle.manager import lifecycle_manager
            
            # Тест статистики
            stats = lifecycle_manager.get_stats()
            
            print("✅ Lifecycle manager создан")
            print(f"   Initial tokens checked: {stats.get('initial_tokens_checked', 0)}")
            print(f"   Active tokens checked: {stats.get('active_tokens_checked', 0)}")
            print(f"   Tokens activated: {stats.get('tokens_activated', 0)}")
            print(f"   Tokens archived: {stats.get('tokens_archived', 0)}")
            print(f"   Errors: {stats.get('errors', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования lifecycle manager: {e}")
            return False

    async def test_activation_logic(self) -> bool:
        """Тест логики активации токенов"""
        print("\n🔍 ТЕСТ ЛОГИКИ АКТИВАЦИИ")
        print("=" * 35)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест БД")
            return True
        
        try:
            from app.database import SessionLocal
            from app.core.lifecycle.manager import lifecycle_manager
            from app.crud import token_crud, system_crud
            from app.models.token import TokenStatus
            
            if not SessionLocal:
                print("❌ База данных не настроена")
                return False
            
            db = SessionLocal()
            
            try:
                # Проверяем параметры конфигурации
                min_liquidity = system_crud.get_value(db, key="MIN_LIQUIDITY_USD", default=500)
                min_tx_count = system_crud.get_value(db, key="MIN_TX_COUNT", default=300)
                
                print(f"✅ Параметры активации загружены:")
                print(f"   MIN_LIQUIDITY_USD: ${min_liquidity}")
                print(f"   MIN_TX_COUNT: {min_tx_count}")
                
                # Проверяем есть ли Initial токены
                initial_tokens = token_crud.get_by_status(db, status=TokenStatus.INITIAL, limit=5)
                
                if initial_tokens:
                    print(f"✅ Найдено {len(initial_tokens)} Initial токенов для тестирования")
                    
                    for token in initial_tokens[:2]:  # Тестируем первые 2
                        print(f"   Тестируем {token.token_address[:8]}...")
                        
                        # Тест логики активации (без реального изменения статуса)
                        should_activate = await lifecycle_manager._should_activate_token(
                            token, min_liquidity, min_tx_count, db
                        )
                        
                        print(f"   Активация: {'✅ ДА' if should_activate else '❌ НЕТ'}")
                else:
                    print("⚠️  Нет Initial токенов для тестирования")
                    print("   Создайте токены через WebSocket или API")
                
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Ошибка тестирования активации: {e}")
            return False

    async def test_archival_logic(self) -> bool:
        """Тест логики архивации по таймауту"""
        print("\n🔍 ТЕСТ ЛОГИКИ АРХИВАЦИИ")
        print("=" * 35)
        
        try:
            from app.core.lifecycle.manager import lifecycle_manager
            from app.models.token import Token, TokenStatus
            from datetime import datetime, timedelta
            
            # Создаем mock токен для тестирования
            class MockToken:
                def __init__(self, hours_ago: int):
                    self.status = TokenStatus.INITIAL
                    self.created_at = datetime.now() - timedelta(hours=hours_ago)
                    self.token_address = f"MockToken{hours_ago}hours"
            
            # Тест токенов разного возраста
            test_cases = [
                (1, False, "1 час - не архивировать"),
                (12, False, "12 часов - не архивировать"), 
                (23, False, "23 часа - не архивировать"),
                (25, True, "25 часов - архивировать"),
                (48, True, "48 часов - архивировать")
            ]
            
            timeout_hours = 24
            
            for hours_ago, should_archive, description in test_cases:
                mock_token = MockToken(hours_ago)
                result = lifecycle_manager._should_archive_by_timeout(mock_token, timeout_hours)
                
                status = "✅" if result == should_archive else "❌"
                print(f"   {status} {description}: {result}")
                
                if result != should_archive:
                    print(f"❌ Ошибка логики архивации для {hours_ago} часов")
                    return False
            
            print("✅ Логика архивации работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования архивации: {e}")
            return False

    async def test_configuration_loading(self) -> bool:
        """Тест загрузки параметров конфигурации"""
        print("\n🔍 ТЕСТ ЗАГРУЗКИ КОНФИГУРАЦИИ")
        print("=" * 42)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест БД")
            return True
        
        try:
            from app.database import SessionLocal
            from app.crud import system_crud
            
            if not SessionLocal:
                print("❌ База данных не настроена")
                return False
            
            db = SessionLocal()
            
            try:
                # Проверяем все параметры lifecycle
                lifecycle_params = [
                    ("MIN_LIQUIDITY_USD", 500),
                    ("MIN_TX_COUNT", 300),
                    ("ARCHIVAL_TIMEOUT_HOURS", 24),
                    ("LOW_SCORE_HOURS", 6),
                    ("LOW_ACTIVITY_CHECKS", 10)
                ]
                
                for param_key, default_value in lifecycle_params:
                    value = system_crud.get_value(db, key=param_key, default=default_value)
                    
                    if value is not None:
                        print(f"✅ {param_key}: {value}")
                    else:
                        print(f"❌ {param_key}: не найден")
                        return False
                
                print("✅ Все параметры конфигурации загружены")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return False


async def quick_lifecycle_test():
    """
    Быстрый тест lifecycle без БД
    """
    print("🔍 БЫСТРЫЙ ТЕСТ LIFECYCLE")
    print("=" * 35)
    
    try:
        from app.core.lifecycle.manager import TokenLifecycleManager
        
        # Создаем менеджер
        manager = TokenLifecycleManager()
        
        # Проверяем статистику
        stats = manager.get_stats()
        
        required_stats = [
            "initial_tokens_checked",
            "active_tokens_checked", 
            "tokens_activated",
            "tokens_archived",
            "tokens_deactivated",
            "errors"
        ]
        
        for stat_key in required_stats:
            if stat_key not in stats:
                print(f"❌ Отсутствует статистика: {stat_key}")
                return False
        
        print("✅ Lifecycle manager создан корректно")
        print(f"   Статистик: {len(stats)} полей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка быстрого теста: {e}")
        return False


def main():
    """
    Главная функция тестирования
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Token Lifecycle Management")
    parser.add_argument(
        "--mode", 
        choices=["quick", "manager", "activation", "archival", "config", "all"], 
        default="quick",
        help="Test mode"
    )
    
    args = parser.parse_args()
    
    print("🧪 ТЕСТИРОВАНИЕ LIFECYCLE СИСТЕМЫ")
    print("=" * 50)
    
    # Запуск тестов
    if args.mode == "quick":
        success = asyncio.run(quick_lifecycle_test())
    elif args.mode == "manager":
        tester = LifecycleTester()
        success = asyncio.run(tester.test_lifecycle_manager())
    elif args.mode == "activation":
        tester = LifecycleTester()
        success = asyncio.run(tester.test_activation_logic())
    elif args.mode == "archival":
        tester = LifecycleTester()
        success = asyncio.run(tester.test_archival_logic())
    elif args.mode == "config":
        tester = LifecycleTester()
        success = asyncio.run(tester.test_configuration_loading())
    elif args.mode == "all":
        tester = LifecycleTester()
        
        tests = [
            ("Быстрый тест", quick_lifecycle_test()),
            ("Lifecycle Manager", tester.test_lifecycle_manager()),
            ("Логика активации", tester.test_activation_logic()),
            ("Логика архивации", tester.test_archival_logic()),
            ("Загрузка конфигурации", tester.test_configuration_loading())
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_coro in tests:
            print(f"\n🔄 {test_name}...")
            try:
                if asyncio.run(test_coro):
                    passed += 1
                    print("✅ Пройден")
                else:
                    failed += 1
                    print("❌ Не пройден")
            except Exception as e:
                failed += 1
                print(f"❌ Исключение: {e}")
        
        print(f"\n📊 ИТОГИ: {passed} пройдено, {failed} не пройдено")
        success = failed == 0
    
    if success:
        print("\n🎉 Тестирование Lifecycle System завершено успешно!")
        
        if args.mode == "quick":
            print("\nДля полного тестирования:")
            print("   python3 scripts/test_lifecycle.py --mode all")
    else:
        print("\n❌ Тестирование Lifecycle System не удалось")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
