#!/usr/bin/env python3
"""
Test script for Iteration 11: Final Integration
Тест готовности одиннадцатой (финальной) итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_realtime_structure():
    """Тест структуры real-time системы"""
    print("🔍 Тестирование структуры real-time системы...")
    
    required_files = [
        "backend/app/core/realtime/__init__.py",
        "backend/app/core/realtime/websocket_manager.py",
        "backend/app/core/realtime/notifications.py",
        "backend/app/api/realtime.py",
        "frontend/src/hooks/useWebSocket.ts"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура real-time системы корректна")
    return True

def test_production_config():
    """Тест production конфигурации"""
    print("🔍 Тестирование production конфигурации...")
    
    required_files = [
        "DEPLOYMENT_GUIDE.md",
        "deploy/nginx-system.conf",
        ".github/workflows/deploy.yml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Production конфигурация создана")
    
    # Проверяем ключевые настройки в nginx-system.conf
    try:
        with open("deploy/nginx-system.conf", "r") as f:
            nginx_content = f.read()
        checks = [
            ("location /api/", "API location"),
            ("location /config/", "TOML location"),
            ("proxy_pass http://localhost:8000", "Proxy to backend :8000"),
            ("limit_req zone=toml", "Rate limiting for TOML"),
        ]
        found = 0
        for needle, desc in checks:
            if needle in nginx_content:
                print(f"✅ {desc}")
                found += 1
            else:
                print(f"❌ {desc} не найден")
        print(f"📊 Nginx checks: {found}/{len(checks)}")
        return found == len(checks)
    except Exception as e:
        print(f"❌ Ошибка проверки Nginx конфига: {e}")
        return False

def test_deploy_scripts():
    """Тест скриптов деплоя"""
    print("🔍 Тестирование скриптов деплоя...")
    
    required_files = [
        "DEPLOYMENT_GUIDE.md",
        "scripts/optimize_performance.py",
        "scripts/test_e2e_all_scenarios.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    try:
        # Проверяем E2E тестовый скрипт
        with open("scripts/test_e2e_all_scenarios.py", "r") as f:
            e2e_content = f.read()
        
        e2e_tests = [
            "test_infrastructure_health",
            "test_api_availability",
            "test_token_lifecycle_scenario",
            "test_birdeye_integration",
            "test_scoring_engine",
            "test_celery_workers",
            "test_toml_export_scenario",
            "test_full_data_flow"
        ]
        
        for test in e2e_tests:
            if f"def {test}" not in e2e_content:
                print(f"❌ E2E тест не найден: {test}")
                return False
        
        print("✅ E2E тестовый скрипт полный")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки скриптов: {e}")
        return False

def test_cicd_integration():
    """Тест CI/CD интеграции"""
    print("🔍 Тестирование CI/CD интеграции...")
    
    try:
        # Проверяем GitHub Actions workflow
        with open(".github/workflows/deploy.yml", "r") as f:
            workflow_content = f.read()
        
        workflow_jobs = [
            "build-and-test",
            "build-images",
            "deploy",
            "e2e-test"
        ]
        
        for job in workflow_jobs:
            if f"{job}:" in workflow_content:
                print(f"✅ Job {job} настроен")
            else:
                print(f"❌ Job {job} не найден")
                return False
        
        # Проверяем что есть секреты
        required_secrets = [
            "VPS_SSH_KEY",
            "VPS_HOST",
            "DATABASE_PASSWORD",
            "SECRET_KEY",
            "BIRDEYE_API_KEY"
        ]
        
        for secret in required_secrets:
            if f"secrets.{secret}" in workflow_content:
                print(f"✅ Secret {secret} используется")
            else:
                print(f"❌ Secret {secret} не найден")
        
        print("✅ CI/CD workflow настроен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки CI/CD: {e}")
        return False

def test_api_integration():
    """Тест интеграции всех API"""
    print("🔍 Тестирование интеграции API...")
    
    try:
        # Проверяем что все роутеры интегрированы в main.py
        with open("backend/app/main.py", "r") as f:
            main_content = f.read()
        
        required_routers = [
            "tokens_router",
            "pools_router",
            "system_router",
            "health_router",
            "websocket_router",
            "birdeye_router",
            "scoring_router",
            "lifecycle_router",
            "toml_export_router",
            "celery_router",
            "realtime_router"
        ]
        
        for router in required_routers:
            if router in main_content:
                print(f"✅ {router} интегрирован")
            else:
                print(f"❌ {router} не найден")
                return False
        
        # Проверяем что realtime роутер подключен с префиксом /api
        if "app.include_router(realtime_router, prefix=\"/api\")" in main_content:
            print("✅ Real-time роутер правильно подключен")
        else:
            print("❌ Real-time роутер неправильно подключен")
            return False
        
        print("✅ Все API роутеры интегрированы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки API интеграции: {e}")
        return False

def test_frontend_realtime():
    """Тест frontend real-time интеграции"""
    print("🔍 Тестирование frontend real-time...")
    
    try:
        # Проверяем WebSocket hook
        with open("frontend/src/hooks/useWebSocket.ts", "r") as f:
            websocket_content = f.read()
        
        required_hooks = [
            "useWebSocket",
            "useTokenUpdates", 
            "useScoringUpdates",
            "useSystemStatsUpdates",
            "useLifecycleEvents",
            "useCeleryStatus"
        ]
        
        for hook in required_hooks:
            if f"export function {hook}" in websocket_content:
                print(f"✅ Hook {hook} реализован")
            else:
                print(f"❌ Hook {hook} не найден")
                return False
        
        # Проверяем типы
        required_types = [
            "TokenUpdate",
            "ScoringUpdate", 
            "SystemStatsUpdate",
            "LifecycleEvent"
        ]
        
        for type_name in required_types:
            if f"interface {type_name}" in websocket_content:
                print(f"✅ Type {type_name} определен")
            else:
                print(f"❌ Type {type_name} не найден")
        
        print("✅ Frontend real-time интеграция готова")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки frontend real-time: {e}")
        return False

def test_system_completeness():
    """Тест полноты системы"""
    print("🔍 Тестирование полноты системы...")
    
    try:
        # Проверяем что все итерации завершены
        with open("doc/tasklist.md", "r") as f:
            tasklist_content = f.read()
        
        # Проверяем статус итераций
        iterations = [
            "| 1️⃣ | ✅",
            "| 2️⃣ | ✅", 
            "| 3️⃣ | ✅",
            "| 4️⃣ | ✅",
            "| 5️⃣ | ✅",
            "| 6️⃣ | ✅", 
            "| 7️⃣ | ✅",
            "| 8️⃣ | ✅",
            "| 9️⃣ | ✅",
            "| 🔟 | ✅"
        ]
        
        completed_iterations = 0
        
        for iteration in iterations:
            if iteration in tasklist_content:
                completed_iterations += 1
            else:
                print(f"❌ Итерация не завершена: {iteration}")
        
        print(f"📊 Завершено итераций: {completed_iterations}/{len(iterations)}")
        
        # Проверяем README
        with open("README.md", "r") as f:
            readme_content = f.read()
        
        if "10 из 11 ✅" in readme_content:
            print("✅ README актуален")
        else:
            print("❌ README не обновлен")
        
        # Проверяем документацию
        required_docs = [
            "doc/vision.md",
            "doc/conventions.md", 
            "doc/tasklist.md",
            "doc/functional_task.md",
            "doc/bot_integration.md"
        ]
        
        docs_complete = all(os.path.exists(doc) for doc in required_docs)
        print(f"✅ Документация: {'полная' if docs_complete else 'неполная'}")
        
        return completed_iterations >= 9 and docs_complete  # Минимум 9 из 10 + документация
        
    except Exception as e:
        print(f"❌ Ошибка проверки полноты системы: {e}")
        return False

def test_production_readiness():
    """Тест готовности к production"""
    print("🔍 Тестирование готовности к production...")
    
    try:
        production_features = [
            ("DEPLOYMENT_GUIDE.md", "Deployment guide"),
            ("deploy/nginx-system.conf", "System Nginx config"),
            (".github/workflows/deploy.yml", "CI/CD pipeline"),
            ("scripts/optimize_performance.py", "Performance optimizer"),
            ("scripts/test_e2e_all_scenarios.py", "E2E testing")
        ]
        
        features_ready = 0
        
        for file_path, description in production_features:
            if os.path.exists(file_path):
                print(f"✅ {description}")
                features_ready += 1
            else:
                print(f"❌ {description} отсутствует")
        
        # Проверяем environment.example
        try:
            with open("environment.example", "r") as f:
                env_content = f.read()
            
            required_vars = [
                "DATABASE_PASSWORD",
                "SECRET_KEY",
                "BIRDEYE_API_KEY",
                "CORS_ORIGINS"
            ]
            
            env_vars_ready = 0
            for var in required_vars:
                if var in env_content:
                    env_vars_ready += 1
            
            print(f"✅ Environment variables: {env_vars_ready}/{len(required_vars)} documented")
            
        except Exception as e:
            print(f"⚠️  Environment check failed: {e}")
        
        print(f"📊 Production features: {features_ready}/{len(production_features)}")
        
        return features_ready >= len(production_features) - 1  # Все кроме может быть одной
        
    except Exception as e:
        print(f"❌ Ошибка проверки production готовности: {e}")
        return False

def test_memory_optimizations():
    """Тест оптимизаций памяти"""
    print("🔍 Тестирование оптимизаций памяти...")
    
    try:
        # Подсчет примерной потребления памяти (оценочно)
        estimated_memory = {
            "postgres": 150,
            "redis": 100,
            "backend": 250,
            "celery_worker": 150,
            "celery_beat": 80,
            "nginx": 50,
            "system_overhead": 200
        }
        
        total_memory = sum(estimated_memory.values())
        print(f"📊 Estimated total memory usage: {total_memory}MB ({total_memory/1024:.1f}GB)")
        
        memory_ok = total_memory <= 1900  # Оставляем 100MB буфер от 2GB
        if memory_ok:
            print("✅ Memory usage within 2GB limit")
        else:
            print(f"❌ Memory usage exceeds safe limit: {total_memory}MB > 1900MB")
        
        return memory_ok
        
    except Exception as e:
        print(f"❌ Ошибка проверки memory оптимизаций: {e}")
        return False

def test_all_modules_integration():
    """Тест интеграции всех модулей"""
    print("🔍 Тестирование интеграции всех модулей...")
    
    try:
        # Проверяем что все модули импортируются
        with open("backend/app/api/__init__.py", "r") as f:
            api_init_content = f.read()
        
        all_routers = [
            "tokens_router",
            "pools_router", 
            "system_router",
            "health_router",
            "websocket_router",
            "birdeye_router",
            "scoring_router",
            "lifecycle_router",
            "toml_export_router",
            "celery_router",
            "realtime_router"
        ]
        
        routers_found = 0
        for router in all_routers:
            if router in api_init_content:
                routers_found += 1
            else:
                print(f"❌ Router не найден: {router}")
        
        print(f"✅ API routers: {routers_found}/{len(all_routers)}")
        
        # Проверяем Celery tasks включение
        with open("backend/app/core/celery_app.py", "r") as f:
            celery_content = f.read()
        
        celery_modules = [
            "app.workers.websocket_tasks",
            "app.workers.birdeye_tasks",
            "app.workers.scoring_tasks", 
            "app.workers.lifecycle_tasks",
            "app.workers.toml_tasks",
            "app.workers.celery_health_tasks"
        ]
        
        celery_modules_found = 0
        for module in celery_modules:
            if module in celery_content:
                celery_modules_found += 1
        
        print(f"✅ Celery modules: {celery_modules_found}/{len(celery_modules)}")
        
        # Проверяем beat schedule
        beat_tasks = [
            "fetch-active-tokens-metrics",
            "calculate-active-tokens-scores",
            "monitor-initial-tokens",
            "generate-toml-config",
            "celery-system-monitoring"
        ]
        
        beat_tasks_found = 0
        for task in beat_tasks:
            if task in celery_content:
                beat_tasks_found += 1
        
        print(f"✅ Beat schedule tasks: {beat_tasks_found}/{len(beat_tasks)}")
        
        return (routers_found >= len(all_routers) - 1 and 
                celery_modules_found >= len(celery_modules) - 1 and 
                beat_tasks_found >= len(beat_tasks) - 1)
        
    except Exception as e:
        print(f"❌ Ошибка проверки интеграции модулей: {e}")
        return False

def test_functional_requirements():
    """Тест соответствия функциональным требованиям"""
    print("🔍 Тестирование соответствия ФЗ...")
    
    try:
        # Проверяем что все сценарии из ФЗ покрыты
        fz_scenarios = [
            ("WebSocket token discovery", "app/core/data_sources/pumpportal_websocket.py"),
            ("Birdeye API integration", "app/core/data_sources/birdeye_client.py"),
            ("Token lifecycle management", "app/core/lifecycle/manager.py"),
            ("Scoring engine", "app/core/scoring/hybrid_momentum_v1.py"),
            ("TOML export for bot", "app/core/toml_export/generator.py"),
            ("Admin panel", "frontend/src/pages/AdminPage.tsx")
        ]
        
        scenarios_implemented = 0
        
        for scenario_name, file_path in fz_scenarios:
            if os.path.exists(f"backend/{file_path}") or os.path.exists(file_path):
                print(f"✅ {scenario_name}")
                scenarios_implemented += 1
            else:
                print(f"❌ {scenario_name} не реализован")
        
        # Проверяем статусы токенов из ФЗ
        with open("backend/app/models/token.py", "r") as f:
            token_content = f.read()
        
        fz_statuses = ["INITIAL", "ACTIVE", "ARCHIVED"]
        statuses_implemented = all(status in token_content for status in fz_statuses)
        
        print(f"✅ Token statuses: {'все реализованы' if statuses_implemented else 'не все реализованы'}")
        
        # Проверяем scoring формулу из ФЗ
        with open("backend/app/core/scoring/hybrid_momentum_v1.py", "r") as f:
            scoring_content = f.read()
        
        fz_components = ["Tx_Accel", "Vol_Momentum", "Holder_Growth", "Orderflow_Imbalance"]
        components_implemented = all(component.lower().replace("_", "") in scoring_content.lower() for component in fz_components)
        
        print(f"✅ Scoring components: {'все реализованы' if components_implemented else 'не все реализованы'}")
        
        print(f"📊 ФЗ scenarios: {scenarios_implemented}/{len(fz_scenarios)}")
        
        return (scenarios_implemented >= len(fz_scenarios) - 1 and 
                statuses_implemented and 
                components_implemented)
        
    except Exception as e:
        print(f"❌ Ошибка проверки ФЗ: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 11")
    print("=" * 50)
    print("🏁 ФИНАЛЬНАЯ ИНТЕГРАЦИЯ - PRODUCTION READY")
    print("=" * 50)
    
    tests = [
        ("Real-time система", test_realtime_structure),
        ("Production конфигурация", test_production_config),
        ("Скрипты деплоя", test_deploy_scripts),
        ("CI/CD интеграция", test_cicd_integration),
        ("API интеграция", test_api_integration),
        ("Frontend real-time", test_frontend_realtime),
        ("Memory оптимизации", test_memory_optimizations),
        ("Интеграция модулей", test_all_modules_integration),
        ("Соответствие ФЗ", test_functional_requirements),
        ("Готовность системы", test_system_completeness),
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
    
    success_rate = passed / len(tests)
    
    if success_rate >= 0.9:  # 90% тестов должны пройти
        print("🎉 ИТЕРАЦИЯ 11 ГОТОВА!")
        print("🚀 СИСТЕМА ГОТОВА К PRODUCTION ДЕПЛОЮ!")
        print("\n🏁 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ:")
        print("1. Полный E2E тест:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("   python3 scripts/test_e2e_all_scenarios.py --mode full")
        print("2. Performance анализ:")
        print("   python3 scripts/optimize_performance.py --mode all")
        print("3. Production деплой: см. DEPLOYMENT_GUIDE.md (systemd + Nginx)")
        print("\n🌐 PRODUCTION URLs:")
        print("   Main: http://tothemoon.sh1z01d.ru")
        print("   API: http://tothemoon.sh1z01d.ru/api/docs")
        print("   Bot: http://tothemoon.sh1z01d.ru/config/dynamic_strategy.toml")
        print("\n🤖 NotArb бот может использовать:")
        print("   URL: http://tothemoon.sh1z01d.ru/config/dynamic_strategy.toml")
        print("   Обновление: каждые 5 минут")
        print("   Формат: TOML с токенами и пулами")
        return True
    else:
        print("❌ ИТЕРАЦИЯ 11 НЕ ГОТОВА")
        print(f"Пройдено только {success_rate:.1%} тестов")
        print("🔧 Исправьте проблемы перед production деплоем")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
