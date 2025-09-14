#!/usr/bin/env python3
"""
Test script for Iteration 9: TOML Export for Bot
Тест готовности девятой итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_toml_structure():
    """Тест структуры TOML модулей"""
    print("🔍 Тестирование структуры TOML модулей...")
    
    required_files = [
        "backend/app/core/toml_export/__init__.py",
        "backend/app/core/toml_export/generator.py",
        "backend/app/workers/toml_tasks.py",
        "backend/app/api/toml_export.py",
        "scripts/test_toml_export.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура TOML модулей корректна")
    return True

def test_toml_imports():
    """Тест импорта TOML модулей"""
    print("🔍 Тестирование импорта TOML модулей...")
    
    try:
        # Проверяем что toml библиотека доступна
        try:
            import toml
            print("✅ TOML библиотека доступна")
        except ImportError:
            print("❌ TOML библиотека не установлена")
            return False
        
        # Проверяем структуру файлов
        with open("backend/app/core/toml_export/generator.py", "r") as f:
            generator_content = f.read()
        
        required_methods = [
            "generate_dynamic_strategy_toml",
            "_get_top_tokens_for_export",
            "_load_export_config",
            "_build_toml_config",
            "get_export_preview"
        ]
        
        for method in required_methods:
            if f"def {method}" not in generator_content:
                print(f"❌ Метод не найден: {method}")
                return False
        
        print("✅ TOML генератор методы реализованы")
        
        # Проверяем API endpoints
        with open("backend/app/api/toml_export.py", "r") as f:
            api_content = f.read()
        
        if "dynamic_strategy.toml" not in api_content:
            print("❌ Основной TOML endpoint не найден")
            return False
            
        if "PlainTextResponse" not in api_content:
            print("❌ PlainTextResponse не используется для TOML")
            return False
        
        print("✅ TOML API endpoints реализованы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта TOML модулей: {e}")
        return False

def test_celery_integration():
    """Тест интеграции с Celery"""
    print("🔍 Тестирование интеграции с Celery...")
    
    try:
        # Проверяем включение в Celery
        with open("backend/app/core/celery_app.py", "r") as f:
            celery_content = f.read()
        
        if "app.workers.toml_tasks" not in celery_content:
            print("❌ TOML tasks не включены в Celery")
            return False
            
        required_tasks = [
            "generate-toml-config",
            "validate-toml-export",
            "toml-export-stats"
        ]
        
        for task in required_tasks:
            if task not in celery_content:
                print(f"❌ Task не найден в schedule: {task}")
                return False
        
        print("✅ Celery интеграция корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки Celery: {e}")
        return False

def test_api_integration():
    """Тест интеграции API"""
    print("🔍 Тестирование интеграции API...")
    
    try:
        # Проверяем интеграцию TOML роутера
        with open("backend/app/main.py", "r") as f:
            main_content = f.read()
        
        if "toml_export_router" not in main_content:
            print("❌ TOML export роутер не интегрирован в main.py")
            return False
            
        # Проверяем что роутер подключен БЕЗ префикса /api
        if "app.include_router(toml_export_router)" not in main_content:
            print("❌ TOML роутер не подключен без префикса")
            return False
        
        print("✅ API интеграция корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки API: {e}")
        return False

def test_nginx_configuration():
    """Тест Nginx конфигурации"""
    print("🔍 Тестирование Nginx конфигурации...")
    
    try:
        with open("deploy/nginx-system.conf", "r") as f:
            nginx_content = f.read()
        
        # Проверяем настройки для /config/
        if "location /config/" not in nginx_content:
            print("❌ Nginx не настроен для /config/ location")
            return False
            
        if "zone=toml" not in nginx_content:
            print("❌ Rate limiting для TOML не настроен")
            return False
            
        if "expires 5m" not in nginx_content and "expires 1m" not in nginx_content:
            print("❌ Кеширование TOML не настроено")
            return False
        
        if "proxy_pass http://localhost:8000" not in nginx_content:
            print("❌ Nginx не проксирует на backend :8000")
            return False
        
        print("✅ Nginx конфигурация корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки Nginx: {e}")
        return False

def test_requirements_update():
    """Тест обновления requirements.txt"""
    print("🔍 Тестирование обновления requirements...")
    
    try:
        with open("backend/requirements.txt", "r") as f:
            requirements_content = f.read()
        
        if "toml==" not in requirements_content:
            print("❌ TOML библиотека не добавлена в requirements.txt")
            return False
        
        print("✅ Requirements обновлены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки requirements: {e}")
        return False

def test_functional_requirements():
    """Тест соответствия функциональным требованиям"""
    print("🔍 Тестирование соответствия ФЗ...")
    
    try:
        # Проверяем что логика соответствует ФЗ
        with open("backend/app/core/toml_export/generator.py", "r") as f:
            generator_content = f.read()
        
        # Проверяем ключевые элементы ФЗ
        fz_requirements = [
            "status=TokenStatus.ACTIVE",  # Отбор активных токенов
            "min_score_for_config",       # Фильтрация по скору
            "score_value",                # Сортировка по скору
            "limit=top_count",           # Топ-3 (или настраиваемое количество)
            "active_only=True"           # Только активные пулы
        ]
        
        for requirement in fz_requirements:
            if requirement not in generator_content:
                print(f"❌ Требование ФЗ не выполнено: {requirement}")
                return False
        
        print("✅ Соответствие функциональным требованиям")
        
        # Проверяем endpoint URL
        with open("backend/app/api/toml_export.py", "r") as f:
            api_content = f.read()
        
        if "/config/dynamic_strategy.toml" not in api_content:
            print("❌ URL endpoint не соответствует ФЗ")
            return False
        
        print("✅ URL endpoint соответствует ФЗ")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки ФЗ: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 9")
    print("=" * 50)
    
    tests = [
        ("Структура TOML модулей", test_toml_structure),
        ("Импорт TOML модулей", test_toml_imports),
        ("Интеграция с Celery", test_celery_integration),
        ("Интеграция API", test_api_integration),
        ("Конфигурация Nginx", test_nginx_configuration),
        ("Обновление requirements", test_requirements_update),
        ("Соответствие ФЗ", test_functional_requirements),
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
        print("🎉 ИТЕРАЦИЯ 9 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("2. Тестирование TOML:")
        print("   python3 scripts/test_toml_export.py --mode quick")
        print("   python3 scripts/test_toml_export.py --mode all")
        print("3. Проверьте TOML endpoint:")
        print("   curl http://localhost:8000/config/dynamic_strategy.toml")
        print("4. Проверьте API endpoints:")
        print("   - GET /config/preview")
        print("   - GET /config/validate") 
        print("   - GET /config/stats")
        print("   - GET /config/sample")
        print("5. Тест кастомных параметров:")
        print("   curl 'http://localhost:8000/config/dynamic_strategy.toml?min_score=0.8&top_count=5'")
        print("\n🤖 ИНТЕГРАЦИЯ С NOTARB БОТОМ:")
        print("   URL для бота: http://tothemoon.sh1z01d.ru/config/dynamic_strategy.toml")
        print("   Формат: TOML с токенами и пулами")
        print("   Обновление: каждые 5 минут")
        print("   Кеширование: 1 минута")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
