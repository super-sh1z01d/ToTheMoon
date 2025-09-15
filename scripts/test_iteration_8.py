#!/usr/bin/env python3
"""
Test script for Iteration 8: Admin Panel + Lifecycle Fix
Тест готовности восьмой итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_lifecycle_structure():
    """Тест структуры lifecycle модулей"""
    print("🔍 Тестирование структуры lifecycle модулей...")
    
    required_files = [
        "backend/app/core/lifecycle/__init__.py",
        "backend/app/core/lifecycle/manager.py",
        "backend/app/workers/lifecycle_tasks.py",
        "backend/app/api/lifecycle.py",
        "scripts/test_lifecycle.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура lifecycle модулей корректна")
    return True

def test_admin_panel_structure():
    """Тест структуры админ-панели"""
    print("🔍 Тестирование структуры админ-панели...")
    
    required_files = [
        "frontend/src/pages/AdminPage.tsx"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы админ-панели: {missing_files}")
        return False
    
    # Проверяем что AdminPage интегрирована в App.tsx
    try:
        with open("frontend/src/App.tsx", "r") as f:
            app_content = f.read()
        
        if "AdminPage" not in app_content:
            print("❌ AdminPage не импортирована в App.tsx")
            return False
            
        if "admin" not in app_content.lower():
            print("❌ Админ-панель не интегрирована в навигацию")
            return False
        
        print("✅ Структура админ-панели корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки админ-панели: {e}")
        return False

def test_lifecycle_imports():
    """Тест импорта lifecycle модулей"""
    print("🔍 Тестирование импорта lifecycle модулей...")
    
    try:
        # Тест основных классов (без внешних зависимостей)
        from app.models.token import TokenStatus, StatusChangeReason
        
        print("✅ Token статусы и причины импортируются")
        
        # Проверяем структуру файлов
        with open("backend/app/core/lifecycle/manager.py", "r") as f:
            manager_content = f.read()
        
        required_methods = [
            "monitor_initial_tokens",
            "monitor_active_tokens_lifecycle",
            "_should_activate_token",
            "_should_archive_by_timeout",
            "_should_deactivate_by_score"
        ]
        
        for method in required_methods:
            if f"def {method}" not in manager_content:
                print(f"❌ Метод не найден: {method}")
                return False
        
        print("✅ Lifecycle методы реализованы")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта lifecycle модулей: {e}")
        return False

def test_celery_integration():
    """Тест интеграции с Celery"""
    print("🔍 Тестирование интеграции с Celery...")
    
    try:
        # Проверяем включение в Celery
        with open("backend/app/core/celery_app.py", "r") as f:
            celery_content = f.read()
        
        if "app.workers.lifecycle_tasks" not in celery_content:
            print("❌ Lifecycle tasks не включены в Celery")
            return False
            
        required_tasks = [
            "monitor-initial-tokens",
            "monitor-active-lifecycle", 
            "fetch-initial-tokens-metrics"
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
        # Проверяем интеграцию lifecycle роутера
        with open("backend/app/main.py", "r") as f:
            main_content = f.read()
        
        if "lifecycle_router" not in main_content:
            print("❌ Lifecycle роутер не интегрирован в main.py")
            return False
        
        # Проверяем API endpoints
        with open("backend/app/api/lifecycle.py", "r") as f:
            api_content = f.read()
        
        required_endpoints = [
            "@router.get(\"/status\")",
            "@router.post(\"/monitor-initial\")",
            "@router.post(\"/force-status-change\")",
            "@router.get(\"/config\")",
            "@router.put(\"/config/{key}\")"
        ]
        
        for endpoint in required_endpoints:
            if endpoint not in api_content:
                print(f"❌ Endpoint не найден: {endpoint}")
                return False
        
        print("✅ API интеграция корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки API: {e}")
        return False

def test_frontend_integration():
    """Тест интеграции фронтенда"""
    print("🔍 Тестирование интеграции фронтенда...")
    
    try:
        # Проверяем HomePage
        with open("frontend/src/pages/HomePage.tsx", "r") as f:
            home_content = f.read()
        
        if "onNavigateToAdmin" not in home_content:
            print("❌ HomePage не поддерживает навигацию в админку")
            return False
        
        # Проверяем Header
        with open("frontend/src/components/Header.tsx", "r") as f:
            header_content = f.read()
        
        if "onNavigateToAdmin" not in header_content:
            print("❌ Header не поддерживает кнопку админки")
            return False
        
        # Проверяем AdminPage
        with open("frontend/src/pages/AdminPage.tsx", "r") as f:
            admin_content = f.read()
        
        if "system/config" not in admin_content:
            print("❌ AdminPage не использует system config API")
            return False
            
        if "lifecycle" not in admin_content.lower():
            print("❌ AdminPage не содержит lifecycle функциональность")
            return False
        
        print("✅ Frontend интеграция корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки frontend: {e}")
        return False

def test_configuration_coverage():
    """Тест покрытия конфигурации"""
    print("🔍 Тестирование покрытия конфигурации...")
    
    try:
        # Проверяем что все параметры из ФЗ есть в конфигурации
        with open("backend/alembic/versions/20250914_0004_initial_config.py", "r") as f:
            config_content = f.read()
        
        required_params = [
            "MIN_LIQUIDITY_USD",
            "MIN_TX_COUNT",
            "ARCHIVAL_TIMEOUT_HOURS", 
            "LOW_SCORE_HOURS",
            "LOW_ACTIVITY_CHECKS",
            "SCORING_WEIGHTS",
            "EWMA_ALPHA",
            "MIN_SCORE_THRESHOLD"
        ]
        
        for param in required_params:
            if param not in config_content:
                print(f"❌ Параметр не найден в initial config: {param}")
                return False
        
        print("✅ Все параметры конфигурации покрыты")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 8")
    print("=" * 50)
    
    tests = [
        ("Структура lifecycle модулей", test_lifecycle_structure),
        ("Структура админ-панели", test_admin_panel_structure),
        ("Импорт lifecycle модулей", test_lifecycle_imports),
        ("Интеграция с Celery", test_celery_integration),
        ("Интеграция API", test_api_integration),
        ("Интеграция frontend", test_frontend_integration),
        ("Покрытие конфигурации", test_configuration_coverage),
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
        print("🎉 ИТЕРАЦИЯ 8 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("2. Тестирование lifecycle:")
        print("   python3 scripts/test_lifecycle.py --mode quick")
        print("3. Откройте админ-панель:")
        print("   http://localhost:3000 -> Админ-панель")
        print("4. Проверьте API endpoints:")
        print("   - GET /api/lifecycle/status")
        print("   - GET /api/lifecycle/config")
        print("   - POST /api/lifecycle/monitor-initial")
        print("   - GET /api/lifecycle/transitions")
        print("5. Проверьте расписание Celery:")
        print("   journalctl -u tothemoon2-celery-beat -f | grep lifecycle (если настроен systemd)")
        print("\n🚨 КРИТИЧНО: Теперь Initial токены мониторятся!")
        print("   - Initial токены: каждые 10 минут")
        print("   - Активация по ликвидности ≥$500 + TX ≥300")
        print("   - Архивация через 24 часа")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
