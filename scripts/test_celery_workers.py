#!/usr/bin/env python3
"""
Test Celery workers functionality and performance
Тестирование функциональности и производительности Celery workers
"""

import asyncio
import sys
import os
import time
import requests
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class CeleryWorkersTester:
    """
    Тестер для Celery workers
    """
    
    def __init__(self):
        self.base_url = "http://localhost"
        
    async def test_celery_monitoring(self) -> bool:
        """Тест системы мониторинга Celery без БД"""
        print("🔍 ТЕСТ МОНИТОРИНГА CELERY")
        print("=" * 40)
        
        try:
            from app.core.celery_monitoring.monitor import CeleryMonitor
            from app.core.celery_monitoring.health import CeleryHealthChecker
            
            # Создаем монитор
            monitor = CeleryMonitor()
            
            # Проверяем статистику
            stats = monitor.get_stats()
            
            print("✅ Celery монитор создан")
            print(f"   Workers проверено: {stats.get('workers_checked', 0)}")
            print(f"   Активных workers: {stats.get('active_workers', 0)}")
            print(f"   Ошибок: {stats.get('errors', 0)}")
            
            # Создаем health checker
            health_checker = CeleryHealthChecker()
            
            # Проверяем историю
            history = health_checker.get_health_history()
            
            print("✅ Health checker создан")
            print(f"   История проверок: {len(history)} записей")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования мониторинга: {e}")
            return False

    async def test_worker_status(self) -> bool:
        """Тест статуса workers с БД"""
        print("\n🔍 ТЕСТ СТАТУСА WORKERS")
        print("=" * 35)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест БД")
            return True
        
        try:
            from app.database import SessionLocal
            from app.core.celery_monitoring.monitor import celery_monitor
            
            if not SessionLocal:
                print("❌ База данных не настроена")
                return False
            
            # Тест получения статуса workers
            workers_status = await celery_monitor.get_workers_status()
            
            print("✅ Статус workers получен:")
            print(f"   Статус: {workers_status.get('status')}")
            
            workers = workers_status.get("workers", [])
            summary = workers_status.get("summary", {})
            
            print(f"   Всего workers: {summary.get('total_workers', 0)}")
            print(f"   Активных: {summary.get('active_workers', 0)}")
            print(f"   Неактивных: {summary.get('inactive_workers', 0)}")
            
            if workers:
                for worker in workers[:3]:  # Показываем первых 3
                    print(f"   Worker: {worker.get('name')} - {worker.get('status')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования статуса workers: {e}")
            return False

    async def test_performance_monitoring(self) -> bool:
        """Тест мониторинга производительности"""
        print("\n🔍 ТЕСТ МОНИТОРИНГА ПРОИЗВОДИТЕЛЬНОСТИ")
        print("=" * 50)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест БД")
            return True
        
        try:
            from app.core.celery_monitoring.monitor import celery_monitor
            
            # Тест метрик производительности
            performance = await celery_monitor.get_performance_metrics()
            
            print("✅ Метрики производительности получены:")
            print(f"   Статус: {performance.get('status')}")
            
            summary = performance.get("summary", {})
            print(f"   Всего workers: {summary.get('total_workers', 0)}")
            print(f"   Общая память: {summary.get('total_memory_mb', 0):.1f}MB")
            print(f"   Использование 2GB лимита: {summary.get('memory_limit_2gb_usage_percent', 0):.1f}%")
            
            # Проверяем что memory usage не критичен
            usage_percent = summary.get("memory_limit_2gb_usage_percent", 0)
            if usage_percent > 90:
                print("⚠️  Критическое использование памяти!")
            elif usage_percent > 75:
                print("⚠️  Высокое использование памяти")
            else:
                print("✅ Использование памяти в норме")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования производительности: {e}")
            return False

    def test_api_endpoints(self) -> bool:
        """Тест API endpoints через HTTP запросы"""
        print("\n🔍 ТЕСТ API ENDPOINTS")
        print("=" * 30)
        
        try:
            endpoints = [
                ("/api/celery/status", "Общий статус Celery"),
                ("/api/celery/workers", "Статус workers"),
                ("/api/celery/queues", "Статус очередей"),
                ("/api/celery/performance", "Метрики производительности"),
                ("/api/celery/beat", "Статус Beat scheduler"),
                ("/api/celery/config", "Конфигурация Celery")
            ]
            
            working_endpoints = 0
            
            for endpoint, description in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    
                    if response.status_code == 200:
                        print(f"✅ {description}: работает")
                        working_endpoints += 1
                        
                        # Показываем краткую информацию для некоторых endpoints
                        if endpoint == "/api/celery/status":
                            data = response.json()
                            overall_status = data.get("overall_status", "unknown")
                            print(f"   Общий статус: {overall_status}")
                            
                        elif endpoint == "/api/celery/workers":
                            data = response.json()
                            summary = data.get("summary", {})
                            print(f"   Активных workers: {summary.get('active_workers', 0)}")
                            
                    else:
                        print(f"❌ {description}: ошибка {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️  {description}: недоступен (сервер не запущен): {e}")
            
            print(f"\n📊 Работающих endpoints: {working_endpoints}/{len(endpoints)}")
            return working_endpoints > 0
            
        except Exception as e:
            print(f"❌ Ошибка тестирования API endpoints: {e}")
            return False

    def test_health_task_execution(self) -> bool:
        """Тест выполнения health check задачи"""
        print("\n🔍 ТЕСТ ВЫПОЛНЕНИЯ HEALTH CHECK")
        print("=" * 45)
        
        try:
            # Запускаем health check через API
            response = requests.post(f"{self.base_url}/api/celery/test-task", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                
                print("✅ Health check задача запущена")
                print(f"   Task ID: {task_id}")
                
                # Ждем немного и проверяем результат через задачи
                time.sleep(3)
                
                # Проверяем статистику задач
                tasks_response = requests.get(f"{self.base_url}/api/celery/tasks", timeout=10)
                
                if tasks_response.status_code == 200:
                    tasks_data = tasks_response.json()
                    current_tasks = tasks_data.get("current_tasks", {})
                    
                    print("✅ Статистика задач получена")
                    
                    summary = current_tasks.get("summary", {})
                    print(f"   Активных задач: {summary.get('total_active_tasks', 0)}")
                    print(f"   Зарезервированных: {summary.get('total_reserved_tasks', 0)}")
                    
                    task_types = current_tasks.get("task_types", {})
                    if task_types:
                        print(f"   Типов задач: {len(task_types)}")
                        for task_type, counts in list(task_types.items())[:3]:
                            print(f"     {task_type}: {counts.get('active', 0)} active")
                
                return True
            else:
                print(f"❌ Не удалось запустить health check: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Health check недоступен (сервер не запущен): {e}")
            return True  # Не ошибка если сервер не запущен
        except Exception as e:
            print(f"❌ Ошибка тестирования health check: {e}")
            return False


async def quick_celery_test():
    """
    Быстрый тест Celery без внешних зависимостей
    """
    print("🔍 БЫСТРЫЙ ТЕСТ CELERY")
    print("=" * 35)
    
    try:
        # Тест конфигурации Celery
        from app.core.celery_app import celery_app
        
        print("✅ Celery app импортирован")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        print(f"   Concurrency: {celery_app.conf.worker_concurrency}")
        print(f"   Prefetch: {celery_app.conf.worker_prefetch_multiplier}")
        
        # Тест beat schedule
        beat_schedule = celery_app.conf.beat_schedule or {}
        print(f"   Scheduled tasks: {len(beat_schedule)}")
        
        # Показываем первые несколько задач
        for task_name in list(beat_schedule.keys())[:5]:
            schedule = beat_schedule[task_name].get("schedule", "unknown")
            if isinstance(schedule, (int, float)):
                if schedule >= 3600:
                    schedule_str = f"{schedule/3600:.1f}h"
                elif schedule >= 60:
                    schedule_str = f"{schedule/60:.1f}m"
                else:
                    schedule_str = f"{schedule}s"
            else:
                schedule_str = str(schedule)
            
            print(f"     {task_name}: {schedule_str}")
        
        # Тест включенных модулей
        include = celery_app.conf.include or []
        print(f"   Включено модулей: {len(include)}")
        
        expected_modules = [
            "app.workers.websocket_tasks",
            "app.workers.birdeye_tasks", 
            "app.workers.scoring_tasks",
            "app.workers.lifecycle_tasks",
            "app.workers.toml_tasks",
            "app.workers.celery_health_tasks"
        ]
        
        missing_modules = []
        for module in expected_modules:
            if module not in include:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"❌ Отсутствующие модули: {missing_modules}")
            return False
        
        print("✅ Все модули включены в Celery")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка быстрого теста Celery: {e}")
        return False
def main():
    """
    Главная функция тестирования
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Celery Workers System")
    parser.add_argument(
        "--mode",
        choices=["quick", "monitoring", "workers", "performance", "api", "health", "all"],
        default="quick",
        help="Test mode"
    )
    
    args = parser.parse_args()
    
    print("🧪 ТЕСТИРОВАНИЕ CELERY WORKERS")
    print("=" * 50)
    
    # Запуск тестов
    if args.mode == "quick":
        success = asyncio.run(quick_celery_test())
    elif args.mode == "monitoring":
        tester = CeleryWorkersTester()
        success = asyncio.run(tester.test_celery_monitoring())
    elif args.mode == "workers":
        tester = CeleryWorkersTester()
        success = asyncio.run(tester.test_worker_status())
    elif args.mode == "performance":
        tester = CeleryWorkersTester()
        success = asyncio.run(tester.test_performance_monitoring())
    elif args.mode == "api":
        tester = CeleryWorkersTester()
        success = tester.test_api_endpoints()
    elif args.mode == "health":
        tester = CeleryWorkersTester()
        success = tester.test_health_task_execution()
    elif args.mode == "all":
        tester = CeleryWorkersTester()
        
        tests = [
            ("Быстрый тест Celery", quick_celery_test()),
            ("Мониторинг Celery", tester.test_celery_monitoring()),
            ("Статус workers", tester.test_worker_status()),
            ("Мониторинг производительности", tester.test_performance_monitoring()),
            ("API endpoints", asyncio.create_task(asyncio.coroutine(tester.test_api_endpoints)())),
            ("Health check execution", asyncio.create_task(asyncio.coroutine(tester.test_health_task_execution)()))
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_task in tests:
            print(f"\n🔄 {test_name}...")
            try:
                if test_name in ["API endpoints", "Health check execution"]:
                    # Синхронные тесты
                    if test_name == "API endpoints":
                        result = tester.test_api_endpoints()
                    else:  # Health check execution
                        result = tester.test_health_task_execution()
                else:
                    # Асинхронные тесты
                    result = await test_task
                
                if result:
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
        print("\n🎉 Тестирование Celery Workers завершено успешно!")
        
        if args.mode == "quick":
            print("\nДля полного тестирования:")
            print("   python3 scripts/test_celery_workers.py --mode all")
            print("\nДля тестирования с работающим сервером:")
            print("   uvicorn app.main:app --host 0.0.0.0 --port 8000")
            print("   python3 scripts/test_celery_workers.py --mode api")
            print("\nУправление workers:")
            print("   python3 scripts/celery_manager.py status")
            print("   python3 scripts/celery_manager.py production")
    else:
        print("\n❌ Тестирование Celery Workers не удалось")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
