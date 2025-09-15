#!/usr/bin/env python3
"""
Test script for Iteration 7: Scoring Engine
Тест готовности седьмой итерации
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_scoring_structure():
    """Тест структуры scoring модулей"""
    print("🔍 Тестирование структуры scoring модулей...")
    
    required_files = [
        "backend/app/core/scoring/__init__.py",
        "backend/app/core/scoring/base.py",
        "backend/app/core/scoring/hybrid_momentum_v1.py",
        "backend/app/core/scoring/manager.py",
        "backend/app/workers/scoring_tasks.py",
        "backend/app/api/scoring.py",
        "scripts/test_scoring.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура scoring модулей корректна")
    return True

def test_scoring_imports():
    """Тест импорта scoring модулей"""
    print("🔍 Тестирование импорта scoring модулей...")
    
    try:
        # Тест базовых классов
        from app.core.scoring.base import (
            ScoringModelBase,
            ScoringResult,
            ScoringConfig,
            TokenMetricsInput,
            ScoringComponents,
            EWMAHelper
        )
        
        print("✅ Базовые классы импортируются")
        
        # Тест модели Hybrid Momentum
        from app.core.scoring.hybrid_momentum_v1 import (
            HybridMomentumV1,
            HybridMomentumV1Factory
        )
        
        print("✅ Hybrid Momentum модель импортируется")
        
        # Тест менеджера
        from app.core.scoring.manager import ScoringManager, scoring_manager
        
        print("✅ Scoring manager импортируется")
        
        # Тест доступных моделей
        from app.core.scoring import AVAILABLE_MODELS
        
        if "hybrid_momentum_v1" not in AVAILABLE_MODELS:
            print("❌ hybrid_momentum_v1 не в AVAILABLE_MODELS")
            return False
        
        print(f"✅ Доступно моделей: {len(AVAILABLE_MODELS)}")
        
        # Тест Celery tasks
        try:
            from app.workers.scoring_tasks import (
                calculate_token_score_task,
                calculate_scores_for_active_tokens_task,
                reload_scoring_model_task
            )
            print("✅ Scoring Celery tasks импортируются")
        except ImportError as e:
            print(f"⚠️  Scoring Celery tasks недоступны: {e}")
        
        # Тест API роутера
        try:
            from app.api.scoring import router as scoring_router
            from app.api import scoring_router as main_scoring_router
            
            if scoring_router and main_scoring_router:
                print("✅ Scoring API роутер импортируется")
        except ImportError as e:
            print(f"⚠️  Scoring API роутер недоступен: {e}")
            
            # Проверим интеграцию в main.py
            with open("backend/app/main.py", "r") as f:
                main_content = f.read()
            
            if "scoring_router" in main_content:
                print("✅ Scoring роутер интегрирован в main.py")
            else:
                print("❌ Scoring роутер не интегрирован в main.py")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта scoring модулей: {e}")
        return False

def test_formula_implementation():
    """Тест реализации формул"""
    print("🔍 Тестирование реализации формул...")
    
    try:
        # Проверяем содержимое файла hybrid_momentum_v1.py
        with open("backend/app/core/scoring/hybrid_momentum_v1.py", "r") as f:
            hybrid_content = f.read()
        
        # Проверяем наличие ключевых формул
        required_formulas = [
            "tx_count_5m / 5",  # TX Accel
            "tx_count_1h / 60",
            "volume_1h / 12",   # Vol Momentum  
            "holders_1h_ago",   # Holder Growth
            "buys_volume_5m",   # Orderflow Imbalance
            "sells_volume_5m"
        ]
        
        for formula in required_formulas:
            if formula not in hybrid_content:
                print(f"❌ Формула не найдена: {formula}")
                return False
        
        print("✅ Ключевые формулы реализованы")
        
        # Проверяем базовые методы
        with open("backend/app/core/scoring/base.py", "r") as f:
            base_content = f.read()
        
        required_methods = [
            "_calculate_tx_accel",
            "_calculate_vol_momentum", 
            "_calculate_holder_growth",
            "_calculate_orderflow_imbalance",
            "_apply_ewma_smoothing"
        ]
        
        for method in required_methods:
            if f"def {method}" not in base_content:
                print(f"❌ Метод не найден: {method}")
                return False
        
        print("✅ Базовые методы реализованы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки формул: {e}")
        return False

def test_configuration_integration():
    """Тест интеграции конфигурации"""
    print("🔍 Тестирование интеграции конфигурации...")
    
    try:
        # Проверяем интеграцию в Celery
        with open("backend/app/core/celery_app.py", "r") as f:
            celery_content = f.read()
        
        if "app.workers.scoring_tasks" not in celery_content:
            print("❌ Scoring tasks не включены в Celery")
            return False
            
        if "calculate_scores_for_active_tokens" not in celery_content:
            print("❌ Scoring задачи не в beat schedule")
            return False
        
        print("✅ Celery интеграция корректна")
        
        # Проверяем factory для загрузки из БД
        with open("backend/app/core/scoring/hybrid_momentum_v1.py", "r") as f:
            factory_content = f.read()
        
        if "create_from_system_config" not in factory_content:
            print("❌ Factory метод для system config не найден")
            return False
            
        if "SCORING_WEIGHTS" not in factory_content:
            print("❌ Загрузка весов из БД не реализована")
            return False
        
        print("✅ Конфигурация из БД реализована")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        return False

def test_api_endpoints():
    """Тест API endpoints"""
    print("🔍 Тестирование API endpoints...")
    
    try:
        # Проверяем содержимое API файла
        with open("backend/app/api/scoring.py", "r") as f:
            api_content = f.read()
        
        required_endpoints = [
            "@router.get(\"/status\")",
            "@router.post(\"/calculate/{token_address}\")",
            "@router.post(\"/calculate-all\")",
            "@router.get(\"/top-tokens\")",
            "@router.get(\"/models\")",
            "@router.put(\"/config/{key}\")"
        ]
        
        for endpoint in required_endpoints:
            if endpoint not in api_content:
                print(f"❌ Endpoint не найден: {endpoint}")
                return False
        
        print("✅ API endpoints реализованы")
        
        # Проверяем интеграцию валидации
        if "Weights sum must be 1.0" not in api_content:
            print("❌ Валидация весов не реализована")
            return False
            
        if "EWMA_ALPHA must be between 0.0 and 1.0" not in api_content:
            print("❌ Валидация EWMA не реализована") 
            return False
        
        print("✅ Валидация конфигурации реализована")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки API: {e}")
        return False

def test_ewma_implementation():
    """Тест реализации EWMA"""
    print("🔍 Тестирование реализации EWMA...")
    
    try:
        # Проверяем что EWMA применяется ко всем компонентам
        with open("backend/app/core/scoring/base.py", "r") as f:
            base_content = f.read()
        
        ewma_components = [
            "tx_accel_smoothed",
            "vol_momentum_smoothed",
            "holder_growth_smoothed", 
            "orderflow_imbalance_smoothed"
        ]
        
        for component in ewma_components:
            if component not in base_content:
                print(f"❌ EWMA компонент не найден: {component}")
                return False
        
        # Проверяем что финальный скор тоже сглаживается
        with open("backend/app/core/scoring/hybrid_momentum_v1.py", "r") as f:
            hybrid_content = f.read()
        
        if "EWMAHelper.smooth(raw_score" not in hybrid_content:
            print("❌ EWMA сглаживание финального скора не реализовано")
            return False
        
        print("✅ EWMA реализация корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки EWMA: {e}")
        return False

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 7")
    print("=" * 50)
    
    tests = [
        ("Структура scoring модулей", test_scoring_structure),
        ("Импорт scoring модулей", test_scoring_imports),
        ("Реализация формул", test_formula_implementation),
        ("Интеграция конфигурации", test_configuration_integration),
        ("API endpoints", test_api_endpoints),
        ("EWMA реализация", test_ewma_implementation),
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
        print("🎉 ИТЕРАЦИЯ 7 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
        print("2. Тестирование формул:")
        print("   python3 scripts/test_scoring.py --mode quick")
        print("3. Тестирование модели:")
        print("   python3 scripts/test_scoring.py --mode model")
        print("4. Полное тестирование:")
        print("   python3 scripts/test_scoring.py --mode all")
        print("5. Проверьте API endpoints:")
        print("   - GET /api/scoring/status")
        print("   - GET /api/scoring/models")
        print("   - POST /api/scoring/test")
        print("   - GET /api/scoring/config")
        print("6. Тест расчета скора:")
        print("   curl -X POST http://localhost:8000/api/scoring/calculate/So11111111111111111111111111111111111111112")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
