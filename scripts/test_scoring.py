#!/usr/bin/env python3
"""
Test Scoring Engine
Тестирование скоринговой системы
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class ScoringTester:
    """
    Тестер для scoring engine
    """
    
    def __init__(self):
        self.manager = None
        
    async def test_hybrid_momentum_model(self) -> bool:
        """Тест модели Hybrid Momentum v1"""
        print("🔍 ТЕСТ МОДЕЛИ HYBRID MOMENTUM V1")
        print("=" * 50)
        
        try:
            from app.core.scoring.hybrid_momentum_v1 import HybridMomentumV1Factory
            from app.core.scoring.base import TokenMetricsInput
            
            # Создаем модель с настройками по умолчанию
            model = HybridMomentumV1Factory.create_default()
            
            print("✅ Модель создана с настройками по умолчанию")
            print(f"   Модель: {model.MODEL_NAME} v{model.MODEL_VERSION}")
            print(f"   EWMA Alpha: {model.ewma_alpha}")
            print(f"   Веса: {model.weights.to_dict()}")
            
            # Тестовые метрики
            test_metrics = TokenMetricsInput(
                tx_count_5m=150,  # 150 транзакций за 5 минут
                tx_count_1h=1200,  # 1200 транзакций за час
                volume_5m_usd=Decimal("25000"),  # $25k объем за 5м
                volume_1h_usd=Decimal("180000"),  # $180k объем за час
                buys_volume_5m_usd=Decimal("15000"),  # $15k покупки
                sells_volume_5m_usd=Decimal("10000"),  # $10k продажи
                holders_count=2500,  # 2500 держателей
                holders_1h_ago=2450,  # 2450 час назад (+50 рост)
                liquidity_usd=Decimal("750000"),  # $750k ликвидность
                timestamp=datetime.now()
            )
            
            print("\n📊 Тестовые метрики:")
            print(f"   TX 5m: {test_metrics.tx_count_5m}")
            print(f"   TX 1h: {test_metrics.tx_count_1h}")
            print(f"   Volume 5m: ${test_metrics.volume_5m_usd}")
            print(f"   Volume 1h: ${test_metrics.volume_1h_usd}")
            print(f"   Holders: {test_metrics.holders_count} (рост: +{test_metrics.holders_count - test_metrics.holders_1h_ago})")
            print(f"   Buys/Sells: ${test_metrics.buys_volume_5m_usd}/${test_metrics.sells_volume_5m_usd}")
            
            # Расчет скора
            test_token = "TestToken111111111111111111111111111111"
            
            print(f"\n🧮 Расчет скора для {test_token[:8]}...")
            
            result = await model.calculate(test_token, test_metrics)
            
            print("✅ Скор рассчитан:")
            print(f"   Raw Score: {result.score_value:.4f}")
            print(f"   Smoothed Score: {result.score_smoothed:.4f}")
            print(f"   Execution Time: {result.execution_time_ms:.2f}ms")
            
            print("\n📈 Компоненты:")
            components = result.components
            print(f"   TX Accel: {components.tx_accel:.4f} -> {components.tx_accel_smoothed:.4f}")
            print(f"   Vol Momentum: {components.vol_momentum:.4f} -> {components.vol_momentum_smoothed:.4f}")
            print(f"   Holder Growth: {components.holder_growth:.4f} -> {components.holder_growth_smoothed:.4f}")
            print(f"   Orderflow Imbalance: {components.orderflow_imbalance:.4f} -> {components.orderflow_imbalance_smoothed:.4f}")
            
            # Тест второго расчета с EWMA
            print("\n🔄 Тест EWMA сглаживания (второй расчет)...")
            
            # Меняем метрики для второго расчета
            test_metrics.tx_count_5m = 200  # Увеличился импульс
            test_metrics.volume_5m_usd = Decimal("35000")  # Увеличился объем
            
            result2 = await model.calculate(test_token, test_metrics, previous_result=result)
            
            print("✅ Второй расчет с EWMA:")
            print(f"   Raw Score: {result2.score_value:.4f}")
            print(f"   Smoothed Score: {result2.score_smoothed:.4f}")
            print(f"   Score Change: {result2.score_smoothed - result.score_smoothed:+.4f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования модели: {e}")
            return False

    async def test_scoring_manager(self) -> bool:
        """Тест менеджера скоринга"""
        print("\n🔍 ТЕСТ SCORING MANAGER")
        print("=" * 40)
        
        try:
            from app.core.scoring.manager import scoring_manager
            
            # Тест получения доступных моделей
            models = scoring_manager.get_available_models()
            
            print(f"✅ Доступно моделей: {len(models)}")
            for model in models:
                status = "✅" if model.get("available") else "❌"
                print(f"   {status} {model.get('name')}: {model.get('description', 'N/A')}")
            
            # Тест статистики
            stats = scoring_manager.get_stats()
            print(f"\n📊 Статистика менеджера:")
            print(f"   Скоров рассчитано: {stats.get('scores_calculated', 0)}")
            print(f"   Ошибок: {stats.get('errors', 0)}")
            print(f"   Модель загружена: {stats.get('model_loaded')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования менеджера: {e}")
            return False

    async def test_configuration_loading(self) -> bool:
        """Тест загрузки конфигурации"""
        print("\n🔍 ТЕСТ ЗАГРУЗКИ КОНФИГУРАЦИИ")
        print("=" * 45)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест БД")
            return True
        
        try:
            from app.database import SessionLocal
            from app.core.scoring.manager import scoring_manager
            
            if not SessionLocal:
                print("❌ База данных не настроена")
                return False
            
            db = SessionLocal()
            
            try:
                # Тест инициализации из конфигурации
                await scoring_manager.initialize_from_config(db)
                
                if scoring_manager.current_model:
                    print("✅ Модель загружена из конфигурации:")
                    print(f"   Модель: {scoring_manager.model_name}")
                    
                    model_info = await scoring_manager.get_model_info()
                    print(f"   Описание: {model_info.get('description')}")
                    print(f"   EWMA Alpha: {model_info.get('ewma_alpha')}")
                    
                    weights = model_info.get('components', {})
                    print(f"   Компоненты: {len(weights)}")
                    
                    return True
                else:
                    print("❌ Модель не загружена")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return False

    async def test_end_to_end_calculation(self) -> bool:
        """Тест end-to-end расчета скора"""
        print("\n🔍 ТЕСТ END-TO-END РАСЧЕТА")
        print("=" * 40)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем E2E тест")
            return True
        
        try:
            from app.database import SessionLocal
            from app.core.scoring.manager import scoring_manager
            from app.crud import token_crud
            
            if not SessionLocal:
                print("❌ База данных не настроена")
                return False
            
            db = SessionLocal()
            
            try:
                # Ищем токен с метриками
                test_token = "So11111111111111111111111111111111111111112"
                
                token = token_crud.get_by_address(db, token_address=test_token)
                if not token:
                    print(f"⚠️  Токен {test_token} не найден в БД")
                    print("   Создайте токен и добавьте метрики для полного тестирования")
                    return True  # Не ошибка, просто нет данных
                
                print(f"✅ Тестовый токен найден: {token.token_address[:8]}...")
                
                # Тест расчета скора
                result = await scoring_manager.calculate_score_for_token(test_token, db)
                
                if result:
                    print("✅ End-to-end расчет успешен:")
                    print(f"   Скор: {result.score_smoothed:.4f}")
                    print(f"   Модель: {result.model_name}")
                    print(f"   Время выполнения: {result.execution_time_ms:.2f}ms")
                    return True
                else:
                    print("❌ End-to-end расчет не удался")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Ошибка end-to-end теста: {e}")
            return False


async def quick_formula_test():
    """
    Быстрый тест формул без БД
    """
    print("🔍 БЫСТРЫЙ ТЕСТ ФОРМУЛ")
    print("=" * 35)
    
    try:
        from app.core.scoring.base import EWMAHelper, ScoringComponents
        
        # Тест безопасного деления
        print("🧮 Тест математических функций...")
        
        # Нормальное деление
        result1 = EWMAHelper.safe_division(10, 2, default=0)
        if result1 != 5.0:
            print(f"❌ Safe division failed: 10/2 = {result1}, expected 5.0")
            return False
        
        # Деление на ноль
        result2 = EWMAHelper.safe_division(10, 0, default=-1)
        if result2 != -1:
            print(f"❌ Safe division by zero failed: got {result2}, expected -1")
            return False
        
        # Безопасный логарифм
        result3 = EWMAHelper.safe_log(2.718281828, default=0)
        if abs(result3 - 1.0) > 0.001:
            print(f"❌ Safe log failed: log(e) = {result3}, expected ~1.0")
            return False
        
        # Логарифм от нуля
        result4 = EWMAHelper.safe_log(0, default=-999)
        if result4 != -999:
            print(f"❌ Safe log of zero failed: got {result4}, expected -999")
            return False
        
        print("✅ Математические функции работают корректно")
        
        # Тест EWMA
        print("\n🎯 Тест EWMA сглаживания...")
        
        # Первое значение (нет предыдущего)
        smoothed1 = EWMAHelper.smooth(100, None, 0.3)
        if smoothed1 != 100:
            print(f"❌ EWMA first value failed: got {smoothed1}, expected 100")
            return False
        
        # Второе значение (с предыдущим)
        smoothed2 = EWMAHelper.smooth(150, 100, 0.3)
        expected = 0.3 * 150 + 0.7 * 100  # = 45 + 70 = 115
        if abs(smoothed2 - expected) > 0.001:
            print(f"❌ EWMA calculation failed: got {smoothed2}, expected {expected}")
            return False
        
        print("✅ EWMA сглаживание работает корректно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования формул: {e}")
        return False


async def test_model_structure():
    """
    Тест структуры модели
    """
    print("🔍 ТЕСТ СТРУКТУРЫ МОДЕЛИ")
    print("=" * 35)
    
    try:
        from app.core.scoring import AVAILABLE_MODELS
        from app.core.scoring.hybrid_momentum_v1 import HybridMomentumV1
        from app.core.scoring.base import ScoringConfig
        
        # Проверяем доступные модели
        if "hybrid_momentum_v1" not in AVAILABLE_MODELS:
            print("❌ hybrid_momentum_v1 не найдена в AVAILABLE_MODELS")
            return False
        
        print(f"✅ Доступно моделей: {len(AVAILABLE_MODELS)}")
        for model_name in AVAILABLE_MODELS.keys():
            print(f"   • {model_name}")
        
        # Тест создания модели
        config = ScoringConfig(
            model_name="hybrid_momentum_v1",
            weights={"W_tx": 0.25, "W_vol": 0.35, "W_hld": 0.20, "W_oi": 0.20},
            ewma_alpha=0.3,
            min_score_threshold=0.5
        )
        
        model = HybridMomentumV1(config)
        
        print("✅ Модель создана из конфигурации")
        
        # Получаем информацию о модели
        model_info = model.get_model_info()
        
        print(f"✅ Информация о модели получена:")
        print(f"   Название: {model_info['name']}")
        print(f"   Версия: {model_info['version']}")
        print(f"   Компонентов: {len(model_info['components'])}")
        print(f"   Сумма весов: {model_info['weights_sum']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования структуры: {e}")
        return False


def main():
    """
    Главная функция тестирования
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Scoring Engine")
    parser.add_argument(
        "--mode", 
        choices=["quick", "model", "manager", "config", "e2e", "all"], 
        default="quick",
        help="Test mode"
    )
    
    args = parser.parse_args()
    
    print("🧪 ТЕСТИРОВАНИЕ SCORING ENGINE")
    print("=" * 50)
    
    # Запуск тестов
    if args.mode == "quick":
        success = asyncio.run(quick_formula_test())
    elif args.mode == "model":
        tester = ScoringTester()
        success = asyncio.run(tester.test_hybrid_momentum_model())
    elif args.mode == "manager":
        tester = ScoringTester()
        success = asyncio.run(tester.test_scoring_manager())
    elif args.mode == "config":
        tester = ScoringTester()
        success = asyncio.run(tester.test_configuration_loading())
    elif args.mode == "e2e":
        tester = ScoringTester()
        success = asyncio.run(tester.test_end_to_end_calculation())
    elif args.mode == "all":
        tester = ScoringTester()
        
        tests = [
            ("Формулы", quick_formula_test()),
            ("Структура модели", test_model_structure()),
            ("Hybrid Momentum модель", tester.test_hybrid_momentum_model()),
            ("Scoring Manager", tester.test_scoring_manager()),
            ("Загрузка конфигурации", tester.test_configuration_loading()),
            ("End-to-End расчет", tester.test_end_to_end_calculation())
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_coro in tests:
            print(f"\n🔄 {test_name}...")
            try:
                if asyncio.run(test_coro):
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
        print("\n🎉 Тестирование Scoring Engine завершено успешно!")
        
        if args.mode == "quick":
            print("\nДля полного тестирования:")
            print("   python3 scripts/test_scoring.py --mode all")
    else:
        print("\n❌ Тестирование Scoring Engine не удалось")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
