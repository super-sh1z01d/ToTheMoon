#!/usr/bin/env python3
"""
Test script for Iteration 2: Data models and migrations
Тест готовности второй итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """Тест импорта всех моделей"""
    print("🔍 Тестирование импорта моделей...")
    
    try:
        from app.models import (
            Base, Token, TokenStatusHistory, Pool, 
            TokenMetrics, TokenScores, SystemConfig, BirdeyeRawData
        )
        print("✅ Все модели импортируются успешно")
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта моделей: {e}")
        return False

def test_database_connection():
    """Тест подключения к базе данных"""
    print("🔍 Тестирование подключения к БД...")
    
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row[0] == 1:
                print("✅ Подключение к базе данных работает")
                return True
            else:
                print("❌ Неожиданный результат запроса")
                return False
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

def test_models_structure():
    """Тест структуры моделей"""
    print("🔍 Тестирование структуры моделей...")
    
    try:
        from app.models import Token, Pool, TokenMetrics, SystemConfig
        from app.models.token import TokenStatus, StatusChangeReason
        
        # Проверяем наличие ключевых полей
        token_fields = ['id', 'token_address', 'status', 'created_at']
        for field in token_fields:
            if not hasattr(Token, field):
                print(f"❌ Отсутствует поле {field} в модели Token")
                return False
        
        # Проверяем enum'ы
        if len(TokenStatus) != 3:
            print("❌ TokenStatus должен содержать 3 значения")
            return False
            
        if len(StatusChangeReason) != 5:
            print("❌ StatusChangeReason должен содержать 5 значений")
            return False
        
        print("✅ Структура моделей корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки структуры моделей: {e}")
        return False

def test_alembic_files():
    """Тест наличия файлов миграций"""
    print("🔍 Тестирование файлов миграций...")
    
    alembic_files = [
        "backend/alembic.ini",
        "backend/alembic/env.py", 
        "backend/alembic/script.py.mako",
        "backend/alembic/versions/20250914_0001_initial_schema.py",
        "backend/alembic/versions/20250914_0002_metrics_and_scores.py",
        "backend/alembic/versions/20250914_0003_partitioning.py",
        "backend/alembic/versions/20250914_0004_initial_config.py"
    ]
    
    missing_files = []
    for file_path in alembic_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы миграций: {missing_files}")
        return False
    
    print("✅ Все файлы миграций на месте")
    return True

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 2")
    print("=" * 50)
    
    # Проверяем environment
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL не установлен - тесты БД будут пропущены")
        print("   Для полного тестирования настройте .env и запустите uvicorn + миграции")
    
    tests = [
        ("Импорт моделей", test_imports),
        ("Файлы миграций", test_alembic_files),
        ("Структура моделей", test_models_structure),
    ]
    
    # Тест БД только если есть подключение
    if os.getenv("DATABASE_URL"):
        tests.append(("Подключение к БД", test_database_connection))
    
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
        print("🎉 ИТЕРАЦИЯ 2 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. python3 scripts/migrate.py")
        print("2. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("3. Проверьте http://localhost:8000/health, /api/system/stats, /api/tokens")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
