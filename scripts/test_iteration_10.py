#!/usr/bin/env python3
"""
Test script for Iteration 10: Celery Workers Optimization
Тест готовности десятой итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_celery_monitoring_structure():
    """Тест структуры мониторинга Celery"""
    print("🔍 Тестирование структуры мониторинга Celery...")
    
    required_files = [
        "backend/app/core/celery_monitoring/__init__.py",
        "backend/app/core/celery_monitoring/monitor.py",
        "backend/app/core/celery_monitoring/health.py",
        "backend/app/workers/celery_health_tasks.py",
        "backend/app/api/celery_management.py",
        "scripts/celery_manager.py",
        "scripts/test_celery_workers.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура мониторинга Celery корректна")
    return True

def test_performance_optimization():
    """Тест оптимизации производительности"""
    print("🔍 Тестирование оптимизации производительности...")
    
    try:
        # Проверяем Celery конфигурацию
        with open("backend/app/core/celery_app.py", "r") as f:
            celery_content = f.read()
        
        # Оптимизации для 2GB RAM
        optimizations = [
            ("worker_concurrency=1", "Concurrency снижен до 1"),
            ("worker_prefetch_multiplier=1", "Prefetch ограничен"),
            ("worker_max_memory_per_child=100000", "Memory limit на процесс"),
            ("worker_max_tasks_per_child=1000", "Tasks limit на процесс"),
            ("task_acks_late=True", "Late acknowledgment")
        ]
        
        optimizations_found = 0
        
        for optimization, description in optimizations:
            if optimization in celery_content:
                print(f"✅ {description}")
                optimizations_found += 1
            else:
                print(f"❌ {description} не найден")
        
        total_optimizations = len(optimizations)
        print(f"\n📊 Celery оптимизаций найдено: {optimizations_found}/{total_optimizations}")
        
        return optimizations_found >= (total_optimizations * 0.8)  # 80% оптимизаций должно быть
        
    except Exception as e:
        print(f"❌ Ошибка проверки оптимизации: {e}")
        return False

def test_monitoring_integration():
    """Тест интеграции мониторинга"""
    print("🔍 Тестирование интеграции мониторинга...")
    
    try:
        # Проверяем включение health tasks в Celery
        with open("backend/app/core/celery_app.py", "r") as f:
            celery_content = f.read()
        
        if "app.workers.celery_health_tasks" not in celery_content:
            print("❌ Health tasks не включены в Celery")
            return False
        
        # Проверяем мониторинговые задачи в schedule
        monitoring_tasks = [
            "celery-system-monitoring",
            "celery-health-check"
        ]
        
        for task in monitoring_tasks:
            if task not in celery_content:
                print(f"❌ Monitoring task не найден: {task}")
                return False
        
        print("✅ Мониторинговые задачи настроены")
        
        # Проверяем API интеграцию
        with open("backend/app/main.py", "r") as f:
            main_content = f.read()
        
        if "celery_router" not in main_content:
            print("❌ Celery роутер не интегрирован в main.py")
            return False
        
        print("✅ API интеграция корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки интеграции: {e}")
        return False

def test_worker_management():
    """Тест утилит управления workers"""
    print("🔍 Тестирование утилит управления...")
    
    try:
        # Проверяем содержимое celery_manager.py
        with open("scripts/celery_manager.py", "r") as f:
            manager_content = f.read()
        
        required_functions = [
            "start_worker",
            "stop_workers", 
            "restart_workers",
            "get_status",
            "run_production_mode",
            "run_development_mode"
        ]
        
        for function in required_functions:
            if f"def {function}" not in manager_content:
                print(f"❌ Функция не найдена: {function}")
                return False
        
        print("✅ Утилиты управления реализованы")
        
        # Проверяем что есть сигнальные обработчики
        if "signal.SIGTERM" not in manager_content:
            print("❌ Graceful shutdown не реализован")
            return False
        
        print("✅ Graceful shutdown реализован")
        
        # Проверяем оптимизацию для production
        if "concurrency=1" not in manager_content:
            print("❌ Production оптимизация не найдена")
            return False
        
        print("✅ Production оптимизация реализована")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки управления workers: {e}")
        return False

def test_health_checks():
    """Тест health check системы"""
    print("🔍 Тестирование health check системы...")
    
    try:
        # Проверяем содержимое health tasks
        with open("backend/app/workers/celery_health_tasks.py", "r") as f:
            health_content = f.read()
        
        required_checks = [
            "database",     # Проверка БД
            "redis",        # Проверка Redis
            "filesystem",   # Проверка ФС
            "system_resources"  # Проверка ресурсов
        ]
        
        for check in required_checks:
            if f'"{check}"' in health_content:
                print(f"✅ {check.capitalize()} check реализован")
            else:
                print(f"❌ {check.capitalize()} check не найден")
                return False
        
        # Проверяем стресс-тест
        if "stress_test_task" not in health_content:
            print("❌ Stress test task не найден")
            return False
        
        print("✅ Stress test реализован")
        
        # Проверяем API для health checks
        with open("backend/app/api/celery_management.py", "r") as f:
            api_content = f.read()
        
        health_endpoints = [
            "/health-check",
            "/ping-workers",
            "/stress-test",
            "/diagnose"
        ]
        
        for endpoint in health_endpoints:
            if endpoint not in api_content:
                print(f"❌ Health endpoint не найден: {endpoint}")
                return False
        
        print("✅ Health check API endpoints реализованы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки health checks: {e}")
        return False

def test_requirements_update():
    """Тест обновления requirements"""
    print("🔍 Тестирование обновления requirements...")
    
    try:
        with open("backend/requirements.txt", "r") as f:
            requirements_content = f.read()
        
        if "psutil==" not in requirements_content:
            print("❌ psutil не добавлен в requirements.txt")
            return False
        
        print("✅ psutil добавлен для системного мониторинга")
        
        # Проверяем что toml тоже есть (из предыдущей итерации)
        if "toml==" not in requirements_content:
            print("❌ toml отсутствует в requirements.txt")
            return False
        
        print("✅ Requirements обновлены корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки requirements: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 10")
    print("=" * 50)
    
    tests = [
        ("Структура мониторинга Celery", test_celery_monitoring_structure),
        ("Оптимизация производительности", test_performance_optimization),
        ("Интеграция мониторинга", test_monitoring_integration),
        ("Управление workers", test_worker_management),
        ("Health check система", test_health_checks),
        ("Обновление requirements", test_requirements_update),
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
        print("🎉 ИТЕРАЦИЯ 10 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("2. Тестирование Celery workers:")
        print("   python3 scripts/test_celery_workers.py --mode quick")
        print("   python3 scripts/test_celery_workers.py --mode all")
        print("3. Управление workers:")
        print("   python3 scripts/celery_manager.py status")
        print("   python3 scripts/celery_manager.py production")
        print("4. Проверьте API endpoints:")
        print("   - GET /api/celery/status")
        print("   - GET /api/celery/workers")
        print("   - GET /api/celery/performance")
        print("   - POST /api/celery/health-check")
        print("   - POST /api/celery/stress-test")
        print("5. Мониторинг производительности:")
        print("   curl http://localhost:8000/api/celery/performance")
        print("   ps aux | grep celery")
        print("\n⚡ ОПТИМИЗАЦИЯ ДЛЯ 2GB RAM:")
        print("   • Worker concurrency: 1 (вместо 2)")
        print("   • Memory limit: 100MB на процесс")
        print("   • Автоперезапуск при превышении memory")
        print("   • Graceful shutdown с таймаутами")
        print("   • Health checks каждые 10 минут")
        print("   • Отключены gossip и mingle")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
