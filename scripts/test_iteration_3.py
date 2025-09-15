#!/usr/bin/env python3
"""
Test script for Iteration 3: FastAPI basic server
Тест готовности третьей итерации
"""

import os
import sys
import json
import time
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_api_structure():
    """Тест структуры API"""
    print("🔍 Тестирование структуры API...")
    
    try:
        # Проверяем импорт роутеров
        from app.api import tokens_router, pools_router, system_router, health_router
        
        # Проверяем схемы
        from app.schemas import TokenCreate, TokenResponse, PoolCreate, SystemStatsResponse
        
        # Проверяем CRUD
        from app.crud import token_crud, pool_crud, system_crud
        
        print("✅ Структура API корректна")
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта API компонентов: {e}")
        return False

def test_fastapi_app():
    """Тест FastAPI приложения"""
    print("🔍 Тестирование FastAPI приложения...")
    
    try:
        from app.main import app
        
        # Проверяем, что приложение создано
        if app is None:
            print("❌ FastAPI приложение не создано")
            return False
        
        # Проверяем роутеры
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/health", "/info", "/api/tokens", "/api/pools", 
            "/api/system/config", "/api/system/stats"
        ]
        
        missing_routes = []
        for expected_route in expected_routes:
            if not any(expected_route in route for route in routes):
                missing_routes.append(expected_route)
        
        if missing_routes:
            print(f"❌ Отсутствуют роутеры: {missing_routes}")
            return False
        
        print("✅ FastAPI приложение настроено корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования FastAPI: {e}")
        return False

def test_database_integration():
    """Тест интеграции с базой данных"""
    print("🔍 Тестирование интеграции с БД...")
    
    try:
        from app.database import get_db, SessionLocal
        
        if not SessionLocal:
            print("⚠️  База данных не сконфигурирована (нет DATABASE_URL)")
            return True  # Это OK для тестов без БД
        
        # Тестируем dependency
        db_gen = get_db()
        db = next(db_gen)
        
        # Простой запрос
        from sqlalchemy import text
        result = db.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        
        db.close()
        
        if row[0] == 1:
            print("✅ Интеграция с БД работает")
            return True
        else:
            print("❌ Неожиданный результат от БД")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка интеграции с БД: {e}")
        return False

def test_schemas_validation():
    """Тест валидации Pydantic схем"""
    print("🔍 Тестирование валидации схем...")
    
    try:
        from app.schemas.token import TokenCreate, TokenResponse
        from app.schemas.pool import PoolCreate
        
        # Тест создания токена - валидные данные
        valid_token = TokenCreate(token_address="So11111111111111111111111111111111111111112")
        
        # Тест создания токена - невалидные данные
        try:
            invalid_token = TokenCreate(token_address="short")
            print("❌ Валидация токена не работает - принимает короткий адрес")
            return False
        except ValueError:
            pass  # Ожидаемая ошибка
        
        # Тест создания пула - валидные данные
        valid_pool = PoolCreate(
            pool_address="So11111111111111111111111111111111111111112",
            dex_name="raydium",
            token_id="123e4567-e89b-12d3-a456-426614174000"
        )
        
        # Тест создания пула - невалидный DEX
        try:
            invalid_pool = PoolCreate(
                pool_address="So11111111111111111111111111111111111111112",
                dex_name="invalid_dex",
                token_id="123e4567-e89b-12d3-a456-426614174000"
            )
            print("❌ Валидация пула не работает - принимает невалидный DEX")
            return False
        except ValueError:
            pass  # Ожидаемая ошибка
        
        print("✅ Валидация схем работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования схем: {e}")
        return False

def test_crud_operations():
    """Тест CRUD операций"""
    print("🔍 Тестирование CRUD операций...")
    
    try:
        from app.crud import token_crud, pool_crud
        from app.models.token import Token, TokenStatus
        
        # Проверяем, что CRUD классы созданы правильно
        if not hasattr(token_crud, 'model'):
            print("❌ token_crud не имеет атрибута model")
            return False
        
        if token_crud.model != Token:
            print("❌ token_crud.model не соответствует модели Token")
            return False
        
        # Проверяем методы
        required_methods = ['get', 'get_multi', 'create', 'update', 'remove']
        for method in required_methods:
            if not hasattr(token_crud, method):
                print(f"❌ token_crud не имеет метода {method}")
                return False
        
        # Проверяем специфичные методы токенов
        token_specific_methods = ['get_by_address', 'get_by_status', 'create_with_history']
        for method in token_specific_methods:
            if not hasattr(token_crud, method):
                print(f"❌ token_crud не имеет метода {method}")
                return False
        
        print("✅ CRUD операции настроены корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования CRUD: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 3")
    print("=" * 50)
    
    # Проверяем environment
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL не установлен - тесты БД будут ограничены")
        print("   Для полного тестирования настройте .env и запустите uvicorn + миграции")
    
    tests = [
        ("Структура API", test_api_structure),
        ("FastAPI приложение", test_fastapi_app),
        ("Валидация схем", test_schemas_validation),
        ("CRUD операции", test_crud_operations),
    ]
    
    # Тест БД только если есть подключение
    if os.getenv("DATABASE_URL"):
        tests.append(("Интеграция с БД", test_database_integration))
    
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
        print("🎉 ИТЕРАЦИЯ 3 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. python3 scripts/migrate.py")
        print("2. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("3. Проверьте API:")
        print("   - GET /health")
        print("   - GET /api/docs") 
        print("   - GET /api/tokens")
        print("   - POST /api/tokens")
        print("   - GET /api/system/stats")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
