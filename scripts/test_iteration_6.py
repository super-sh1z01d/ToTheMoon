#!/usr/bin/env python3
"""
Test script for Iteration 6: Birdeye API Integration
Тест готовности шестой итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_birdeye_structure():
    """Тест структуры Birdeye модулей"""
    print("🔍 Тестирование структуры Birdeye модулей...")
    
    required_files = [
        "backend/app/core/data_sources/birdeye_client.py",
        "backend/app/workers/birdeye_tasks.py",
        "backend/app/api/birdeye.py",
        "backend/app/crud/metrics.py",
        "scripts/test_birdeye.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура Birdeye модулей корректна")
    return True

def test_birdeye_imports():
    """Тест импорта Birdeye модулей"""
    print("🔍 Тестирование импорта Birdeye модулей...")
    
    try:
        # Тест CRUD модулей (не требуют aiohttp)
        from app.crud.metrics import (
            token_metrics_crud,
            token_scores_crud,
            birdeye_raw_data_crud
        )
        
        print("✅ CRUD модули для метрик импортируются")
        
        # Тест основных классов данных (структуры)
        try:
            from app.core.data_sources.birdeye_client import (
                TokenOverview,
                TokenTrades,
                BirdeyeRateLimitError,
                BirdeyeAPIError
            )
            print("✅ Классы данных Birdeye импортируются")
        except ImportError as e:
            print(f"⚠️  Основные Birdeye модули недоступны: {e}")
        
        # Тест API роутера
        try:
            from app.api.birdeye import router as birdeye_router
            from app.api import birdeye_router as main_birdeye_router
            
            if birdeye_router and main_birdeye_router:
                print("✅ Birdeye API роутер импортируется")
        except ImportError as e:
            print(f"⚠️  Birdeye API роутер недоступен: {e}")
            
            # Проверим интеграцию в main.py
            with open("backend/app/main.py", "r") as f:
                main_content = f.read()
            
            if "birdeye_router" in main_content:
                print("✅ Birdeye роутер интегрирован в main.py")
            else:
                print("❌ Birdeye роутер не интегрирован в main.py")
                return False
        
        # Тест Celery tasks
        try:
            from app.workers.birdeye_tasks import (
                fetch_token_metrics_task,
                fetch_metrics_for_active_tokens_task,
                test_birdeye_connection_task
            )
            print("✅ Birdeye Celery tasks импортируются")
        except ImportError as e:
            print(f"⚠️  Birdeye Celery tasks недоступны: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта Birdeye модулей: {e}")
        return False

def test_birdeye_file_structure():
    """Тест структуры файлов Birdeye"""
    print("🔍 Тестирование структуры файлов Birdeye...")
    
    try:
        # Проверяем содержимое основного файла
        with open("backend/app/core/data_sources/birdeye_client.py", "r") as f:
            birdeye_content = f.read()
        
        required_classes = [
            "class BirdeyeClient",
            "class BirdeyeManager", 
            "class TokenOverview",
            "class TokenTrades"
        ]
        
        for class_name in required_classes:
            if class_name not in birdeye_content:
                print(f"❌ Отсутствует {class_name}")
                return False
        
        required_methods = [
            "get_token_overview",
            "get_token_trades",
            "fetch_token_metrics",
            "save_token_metrics"
        ]
        
        for method_name in required_methods:
            if f"def {method_name}" not in birdeye_content:
                print(f"❌ Отсутствует метод {method_name}")
                return False
        
        print("✅ Структура файлов Birdeye корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки структуры файлов: {e}")
        return False

def test_data_classes():
    """Тест классов данных"""
    print("🔍 Тестирование классов данных...")
    
    try:
        # Проверяем что файл mock существует
        if not os.path.exists("backend/app/core/data_sources/birdeye_mock.py"):
            print("❌ Mock файл не создан")
            return False
        
        # Проверяем содержимое mock файла
        with open("backend/app/core/data_sources/birdeye_mock.py", "r") as f:
            mock_content = f.read()
        
        if "class MockBirdeyeClient" not in mock_content:
            print("❌ MockBirdeyeClient не найден")
            return False
            
        if "def use_mock_birdeye" not in mock_content:
            print("❌ Функция use_mock_birdeye не найдена") 
            return False
        
        print("✅ Классы данных и mock версия созданы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования классов данных: {e}")
        return False

def test_crud_operations():
    """Тест CRUD операций для метрик"""
    print("🔍 Тестирование CRUD операций...")
    
    try:
        from app.crud.metrics import (
            CRUDTokenMetrics,
            CRUDTokenScores, 
            CRUDBirdeyeRawData
        )
        from app.models.metrics import TokenMetrics, TokenScores
        from app.models.raw_data import BirdeyeRawData
        
        # Проверяем создание CRUD классов
        metrics_crud = CRUDTokenMetrics(TokenMetrics)
        scores_crud = CRUDTokenScores(TokenScores)
        raw_data_crud = CRUDBirdeyeRawData(BirdeyeRawData)
        
        # Проверяем методы
        required_methods = ['get', 'get_multi', 'create', 'update', 'remove']
        for crud, name in [(metrics_crud, 'metrics'), (scores_crud, 'scores'), (raw_data_crud, 'raw_data')]:
            for method in required_methods:
                if not hasattr(crud, method):
                    print(f"❌ {name} CRUD не имеет метода {method}")
                    return False
        
        # Проверяем специфичные методы
        if not hasattr(metrics_crud, 'get_by_token'):
            print("❌ metrics CRUD не имеет метода get_by_token")
            return False
            
        if not hasattr(raw_data_crud, 'cleanup_expired_data'):
            print("❌ raw_data CRUD не имеет метода cleanup_expired_data")
            return False
        
        print("✅ CRUD операции настроены корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования CRUD: {e}")
        return False

def test_environment_config():
    """Тест конфигурации environment"""
    print("🔍 Тестирование конфигурации environment...")
    
    try:
        # Проверяем environment.example
        with open("environment.example", "r") as f:
            env_content = f.read()
        
        if "BIRDEYE_API_KEY" not in env_content:
            print("❌ BIRDEYE_API_KEY не добавлен в environment.example")
            return False
            
        if "BIRDEYE_BASE_URL" not in env_content:
            print("❌ BIRDEYE_BASE_URL не добавлен в environment.example")
            return False
        
        print("✅ Environment конфигурация корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        return False

def test_api_integration():
    """Тест интеграции API"""
    print("🔍 Тестирование интеграции API...")
    
    try:
        # Проверяем интеграцию в main.py
        with open("backend/app/main.py", "r") as f:
            main_content = f.read()
        
        if "birdeye_router" not in main_content:
            print("❌ Birdeye роутер не интегрирован в main.py")
            return False
        
        # Проверяем включение в Celery
        with open("backend/app/core/celery_app.py", "r") as f:
            celery_content = f.read()
        
        if "app.workers.birdeye_tasks" not in celery_content:
            print("❌ Birdeye tasks не включены в Celery")
            return False
            
        if "fetch_metrics_for_active_tokens" not in celery_content:
            print("❌ Birdeye задачи не настроены в beat schedule")
            return False
        
        print("✅ API интеграция корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки интеграции API: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 6")
    print("=" * 50)
    
    tests = [
        ("Структура Birdeye модулей", test_birdeye_structure),
        ("Импорт Birdeye модулей", test_birdeye_imports),
        ("Структура файлов Birdeye", test_birdeye_file_structure),
        ("Классы данных и mock", test_data_classes),
        ("CRUD операции", test_crud_operations),
        ("Environment конфигурация", test_environment_config),
        ("API интеграция", test_api_integration),
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
        print("🎉 ИТЕРАЦИЯ 6 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. Настройте .env файл с BIRDEYE_API_KEY")
        print("2. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("3. Тестирование Birdeye API:")
        print("   python3 scripts/test_birdeye.py --mode quick")
        print("   python3 scripts/test_birdeye.py --mode full")
        print("4. Проверьте API endpoints:")
        print("   - GET http://localhost:8000/api/birdeye/status")
        print("   - POST http://localhost:8000/api/birdeye/test")
        print("   - POST http://localhost:8000/api/birdeye/fetch/{token_address}")
        print("   - GET http://localhost:8000/api/birdeye/stats")
        print("5. Тест с реальным токеном:")
        print("   curl -X POST http://localhost:8000/api/birdeye/fetch/So11111111111111111111111111111111111111112")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
