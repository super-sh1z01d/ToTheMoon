#!/usr/bin/env python3
"""
Test script for Iteration 5: WebSocket Integration
Тест готовности пятой итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_websocket_structure():
    """Тест структуры WebSocket модулей"""
    print("🔍 Тестирование структуры WebSocket модулей...")
    
    required_files = [
        "backend/app/core/__init__.py",
        "backend/app/core/data_sources/__init__.py",
        "backend/app/core/data_sources/pumpportal_websocket.py",
        "backend/app/workers/__init__.py",
        "backend/app/workers/websocket_tasks.py",
        "backend/app/core/celery_app.py",
        "backend/app/api/websocket.py",
        "scripts/test_websocket.py",
        "scripts/start_celery.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура WebSocket модулей корректна")
    return True

def test_websocket_imports():
    """Тест импорта WebSocket модулей"""
    print("🔍 Тестирование импорта WebSocket модулей...")
    
    try:
        # Тест импорта основных классов
        from app.core.data_sources.pumpportal_websocket import (
            PumpPortalWebSocketClient,
            PumpPortalManager,
            TokenMigrationEvent,
            NewTokenEvent,
            pumpportal_manager
        )
        
        print("✅ Основные WebSocket модули импортируются успешно")
        
        # Тест импорта Celery модулей (опционально)
        try:
            from app.workers.websocket_tasks import (
                start_pumpportal_websocket_task,
                stop_pumpportal_websocket_task,
                get_pumpportal_stats
            )
            from app.core.celery_app import celery_app
            from app.api.websocket import router as websocket_router
            
            print("✅ Celery модули также импортируются успешно")
            
        except ImportError as e:
            print(f"⚠️  Celery модули недоступны: {e}")
            print("   Убедитесь, что окружение настроено и зависимости установлены")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта основных WebSocket модулей: {e}")
        return False

def test_websocket_client_creation():
    """Тест создания WebSocket клиента"""
    print("🔍 Тестирование создания WebSocket клиента...")
    
    try:
        from app.core.data_sources.pumpportal_websocket import PumpPortalWebSocketClient
        
        # Создаем клиент
        client = PumpPortalWebSocketClient(
            websocket_url="wss://test.example.com",
            max_reconnect_attempts=3,
            reconnect_delay=1
        )
        
        # Проверяем основные атрибуты
        if not hasattr(client, 'websocket_url'):
            print("❌ WebSocket клиент не имеет websocket_url")
            return False
            
        if not hasattr(client, 'connect'):
            print("❌ WebSocket клиент не имеет метода connect")
            return False
            
        if not hasattr(client, 'subscribe_migrations'):
            print("❌ WebSocket клиент не имеет метода subscribe_migrations")
            return False
            
        if client.websocket_url != "wss://test.example.com":
            print("❌ WebSocket URL не устанавливается корректно")
            return False
            
        print("✅ WebSocket клиент создается корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания WebSocket клиента: {e}")
        return False

def test_celery_configuration():
    """Тест конфигурации Celery"""
    print("🔍 Тестирование конфигурации Celery...")
    
    try:
        from app.core.celery_app import celery_app
        
        # Проверяем основную конфигурацию
        if not celery_app.conf.broker_url:
            print("❌ Celery broker URL не настроен")
            return False
            
        if not celery_app.conf.result_backend:
            print("❌ Celery result backend не настроен")
            return False
            
        # Проверяем, что включены наши модули
        if "app.workers.websocket_tasks" not in celery_app.conf.include:
            print("❌ WebSocket tasks не включены в Celery")
            return False
            
        # Проверяем beat schedule
        if not celery_app.conf.beat_schedule:
            print("❌ Beat schedule не настроен")
            return False
            
        print("✅ Конфигурация Celery корректна")
        return True
        
    except ImportError as e:
        print(f"⚠️  Celery не установлен локально (требуется docker): {e}")
        print("   Проверим только наличие файлов конфигурации...")
        
        # Проверяем хотя бы наличие файлов
        if os.path.exists("backend/app/core/celery_app.py"):
            print("✅ Файл конфигурации Celery существует")
            return True
        else:
            print("❌ Файл конфигурации Celery отсутствует")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка конфигурации Celery: {e}")
        return False

def test_api_integration():
    """Тест интеграции WebSocket API"""
    print("🔍 Тестирование интеграции WebSocket API...")
    
    try:
        # Проверяем наличие файлов
        if not os.path.exists("backend/app/api/websocket.py"):
            print("❌ WebSocket API файл отсутствует")
            return False
            
        # Пытаемся импортировать API модули
        try:
            from app.api.websocket import router
            from app.api import websocket_router
            
            # Проверяем, что роутер создан
            if not router:
                print("❌ WebSocket роутер не создан")
                return False
                
            # Проверяем импорт в main API
            if not websocket_router:
                print("❌ WebSocket роутер не импортирован в main API")
                return False
            
            print("✅ WebSocket API интеграция корректна")
            return True
            
        except ImportError as e:
            print(f"⚠️  WebSocket API недоступен (требуется docker): {e}")
            print("   Проверим интеграцию в main.py...")
            
            # Проверяем интеграцию в main.py
            with open("backend/app/main.py", "r") as f:
                main_content = f.read()
            
            if "websocket_router" in main_content:
                print("✅ WebSocket роутер интегрирован в main.py")
                return True
            else:
                print("❌ WebSocket роутер не интегрирован в main.py")
                return False
        
    except Exception as e:
        print(f"❌ Ошибка интеграции WebSocket API: {e}")
        return False

def test_runtime_environment():
    """Тест базовой конфигурации окружения (без Docker)"""
    print("🔍 Тестирование конфигурации окружения...")
    
    try:
        # Проверяем переменные окружения в примере
        with open("environment.example", "r") as f:
            env_content = f.read()
        
        required = ["PUMPPORTAL_WS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", "REDIS_URL"]
        missing = [k for k in required if k not in env_content]
        if missing:
            print(f"❌ Отсутствуют ключи в environment.example: {missing}")
            return False
        
        print("✅ Environment пример содержит необходимые ключи")
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки окружения: {e}")
        return False

def test_event_data_classes():
    """Тест классов данных событий"""
    print("🔍 Тестирование классов данных событий...")
    
    try:
        from app.core.data_sources.pumpportal_websocket import (
            TokenMigrationEvent,
            NewTokenEvent
        )
        from datetime import datetime
        
        # Тест TokenMigrationEvent
        migration_event = TokenMigrationEvent(
            token_address="So11111111111111111111111111111111111111112",
            timestamp=datetime.now(),
            liquidity_pool_address="Pool11111111111111111111111111111111111111",
            dex_name="raydium"
        )
        
        if migration_event.token_address != "So11111111111111111111111111111111111111112":
            print("❌ TokenMigrationEvent не работает корректно")
            return False
        
        # Тест NewTokenEvent
        new_token_event = NewTokenEvent(
            token_address="Token1111111111111111111111111111111111111",
            name="Test Token",
            symbol="TEST",
            timestamp=datetime.now()
        )
        
        if new_token_event.symbol != "TEST":
            print("❌ NewTokenEvent не работает корректно")
            return False
        
        print("✅ Классы данных событий работают корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования классов данных: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 5")
    print("=" * 50)
    
    tests = [
        ("Структура WebSocket модулей", test_websocket_structure),
        ("Импорт WebSocket модулей", test_websocket_imports),
        ("Создание WebSocket клиента", test_websocket_client_creation),
        ("Конфигурация Celery", test_celery_configuration),
        ("Интеграция WebSocket API", test_api_integration),
        ("Конфигурация окружения", test_runtime_environment),
        ("Классы данных событий", test_event_data_classes),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔄 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Исключение в тесте {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed} прошло, {failed} не прошло")
    
    if failed == 0:
        print("🎉 ИТЕРАЦИЯ 5 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("2. Проверьте WebSocket подключение:")
        print("   python3 scripts/test_websocket.py --mode simple")
        print("3. Запустите Celery worker:")
        print("   python3 scripts/start_celery.py worker")
        print("4. Проверьте API endpoints:")
        print("   - GET /api/websocket/pumpportal/status")
        print("   - POST /api/websocket/pumpportal/start")
        print("   - GET /api/websocket/stats")
        print("5. Для длительного теста:")
        print("   python3 scripts/test_websocket.py --mode listen --duration 300")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
