#!/usr/bin/env python3
"""
Test TOML export for arbitrage bot
Тестирование TOML экспорта для арбитражного бота
"""

import asyncio
import sys
import os
import requests
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class TOMLExportTester:
    """
    Тестер для TOML экспорта
    """
    
    def __init__(self):
        self.base_url = "http://localhost"
        
    async def test_toml_generation(self) -> bool:
        """Тест генерации TOML без БД"""
        print("🔍 ТЕСТ ГЕНЕРАЦИИ TOML")
        print("=" * 35)
        
        try:
            from app.core.toml_export.generator import TOMLConfigGenerator
            
            # Создаем генератор
            generator = TOMLConfigGenerator()
            
            # Проверяем статистику
            stats = generator.get_stats()
            
            print("✅ TOML генератор создан")
            print(f"   TOML сгенерировано: {stats.get('toml_generated', 0)}")
            print(f"   Токенов экспортировано: {stats.get('tokens_exported', 0)}")
            print(f"   Ошибок: {stats.get('errors', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования TOML генератора: {e}")
            return False

    async def test_export_logic(self) -> bool:
        """Тест логики экспорта с БД"""
        print("\n🔍 ТЕСТ ЛОГИКИ ЭКСПОРТА")
        print("=" * 35)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест БД")
            return True
        
        try:
            from app.database import SessionLocal
            from app.core.toml_export.generator import toml_generator
            
            if not SessionLocal:
                print("❌ База данных не настроена")
                return False
            
            db = SessionLocal()
            
            try:
                # Тест загрузки конфигурации
                config_params = await toml_generator._load_export_config(db)
                
                print("✅ Параметры экспорта загружены:")
                print(f"   MIN_SCORE_FOR_CONFIG: {config_params['min_score_for_config']}")
                print(f"   CONFIG_TOP_COUNT: {config_params['config_top_count']}")
                print(f"   SCORING_MODEL: {config_params['scoring_model']}")
                
                # Тест получения топ токенов
                top_tokens = await toml_generator._get_top_tokens_for_export(db, config_params)
                
                print(f"✅ Найдено {len(top_tokens)} токенов для экспорта")
                
                if top_tokens:
                    for i, token_data in enumerate(top_tokens[:3]):
                        print(f"   #{i+1}: Score {token_data['score_value']:.3f}")
                
                # Тест предварительного просмотра
                preview = await toml_generator.get_export_preview(db)
                
                print(f"✅ Предварительный просмотр:")
                print(f"   Активных токенов: {preview.get('export_config', {}).get('active_tokens_count', 0)}")
                print(f"   Токенов к экспорту: {preview.get('total_tokens', 0)}")
                print(f"   Пулов к экспорту: {preview.get('total_pools', 0)}")
                
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Ошибка тестирования логики экспорта: {e}")
            return False

    async def test_toml_format(self) -> bool:
        """Тест формата TOML"""
        print("\n🔍 ТЕСТ ФОРМАТА TOML")
        print("=" * 30)
        
        # Проверяем наличие DATABASE_URL
        if not os.getenv("DATABASE_URL"):
            print("⚠️  DATABASE_URL не установлен - пропускаем тест TOML")
            return True
        
        try:
            from app.database import SessionLocal
            from app.core.toml_export.generator import toml_generator
            import toml
            
            if not SessionLocal:
                print("❌ База данных не настроена")
                return False
            
            db = SessionLocal()
            
            try:
                # Генерируем TOML
                toml_content = await toml_generator.generate_dynamic_strategy_toml(db)
                
                print("✅ TOML контент сгенерирован")
                print(f"   Размер: {len(toml_content)} символов")
                
                # Парсим TOML для валидации формата
                parsed_config = toml.loads(toml_content)
                
                print("✅ TOML формат валиден")
                
                # Проверяем структуру
                required_sections = ["strategy", "tokens", "metadata"]
                for section in required_sections:
                    if section not in parsed_config:
                        print(f"❌ Отсутствует секция: {section}")
                        return False
                
                print("✅ Структура TOML корректна")
                
                # Показываем превью
                strategy = parsed_config.get("strategy", {})
                tokens = parsed_config.get("tokens", [])
                
                print(f"\n📋 Содержимое TOML:")
                print(f"   Стратегия: {strategy.get('name')}")
                print(f"   Модель: {strategy.get('model_name')}")
                print(f"   Токенов: {len(tokens)}")
                print(f"   Минимальный скор: {strategy.get('min_score_threshold')}")
                
                if tokens:
                    print(f"\n📈 Топ токены:")
                    for i, token in enumerate(tokens):
                        print(f"   #{i+1}: {token.get('address', 'unknown')[:8]}... (score: {token.get('score', 0):.3f})")
                
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Ошибка тестирования формата TOML: {e}")
            return False

    def test_api_endpoints(self) -> bool:
        """Тест API endpoints через HTTP запросы"""
        print("\n🔍 ТЕСТ API ENDPOINTS")
        print("=" * 30)
        
        try:
            # Тест preview endpoint
            print("Тестирование /config/preview...")
            
            try:
                response = requests.get(f"{self.base_url}/config/preview", timeout=10)
                
                if response.status_code == 200:
                    print("✅ Preview endpoint работает")
                    
                    data = response.json()
                    print(f"   Токенов к экспорту: {data.get('total_tokens', 0)}")
                    print(f"   Пулов к экспорту: {data.get('total_pools', 0)}")
                else:
                    print(f"❌ Preview endpoint ошибка: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Preview endpoint недоступен (сервер не запущен): {e}")
            
            # Тест validate endpoint
            print("\nТестирование /config/validate...")
            
            try:
                response = requests.get(f"{self.base_url}/config/validate", timeout=10)
                
                if response.status_code == 200:
                    print("✅ Validate endpoint работает")
                    
                    data = response.json()
                    valid = data.get('valid', False)
                    issues = data.get('issues', [])
                    
                    print(f"   Конфигурация валидна: {'✅' if valid else '❌'}")
                    if issues:
                        print(f"   Проблемы: {len(issues)}")
                        for issue in issues[:3]:  # Показываем первые 3
                            print(f"     - {issue}")
                else:
                    print(f"❌ Validate endpoint ошибка: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Validate endpoint недоступен (сервер не запущен): {e}")
            
            # Тест основного TOML endpoint
            print("\nТестирование /config/dynamic_strategy.toml...")
            
            try:
                response = requests.get(f"{self.base_url}/config/dynamic_strategy.toml", timeout=10)
                
                if response.status_code == 200:
                    print("✅ TOML endpoint работает")
                    
                    toml_content = response.text
                    print(f"   Размер TOML: {len(toml_content)} символов")
                    
                    # Проверяем что это валидный TOML
                    import toml
                    try:
                        parsed = toml.loads(toml_content)
                        print(f"   Токенов в TOML: {len(parsed.get('tokens', []))}")
                    except Exception as e:
                        print(f"❌ Невалидный TOML формат: {e}")
                        return False
                        
                    # Проверяем заголовки кеширования
                    cache_control = response.headers.get('Cache-Control', '')
                    if 'max-age' in cache_control:
                        print("✅ Кеширование настроено")
                    else:
                        print("⚠️  Кеширование не настроено")
                else:
                    print(f"❌ TOML endpoint ошибка: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  TOML endpoint недоступен (сервер не запущен): {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования API endpoints: {e}")
            return False


async def quick_toml_test():
    """
    Быстрый тест TOML без БД
    """
    print("🔍 БЫСТРЫЙ ТЕСТ TOML")
    print("=" * 30)
    
    try:
        import toml
        
        # Тест создания простого TOML
        test_config = {
            "strategy": {
                "name": "test_strategy",
                "version": "1.0.0"
            },
            "tokens": [
                {
                    "address": "TestToken1111111111111111111111111111",
                    "score": 0.85,
                    "pools": {
                        "raydium": ["Pool1111111111111111111111111111111111"]
                    }
                }
            ]
        }
        
        # Конвертируем в TOML
        toml_content = toml.dumps(test_config)
        
        print("✅ TOML формат работает")
        print(f"   Размер: {len(toml_content)} символов")
        
        # Парсим обратно для проверки
        parsed_back = toml.loads(toml_content)
        
        if parsed_back == test_config:
            print("✅ TOML парсинг работает корректно")
        else:
            print("❌ TOML парсинг не работает")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка быстрого теста TOML: {e}")
        return False


def main():
    """
    Главная функция тестирования
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test TOML Export for Arbitrage Bot")
    parser.add_argument(
        "--mode", 
        choices=["quick", "generator", "logic", "format", "api", "all"], 
        default="quick",
        help="Test mode"
    )
    
    args = parser.parse_args()
    
    print("🧪 ТЕСТИРОВАНИЕ TOML ЭКСПОРТА")
    print("=" * 50)
    
    # Запуск тестов
    if args.mode == "quick":
        success = asyncio.run(quick_toml_test())
    elif args.mode == "generator":
        tester = TOMLExportTester()
        success = asyncio.run(tester.test_toml_generation())
    elif args.mode == "logic":
        tester = TOMLExportTester()
        success = asyncio.run(tester.test_export_logic())
    elif args.mode == "format":
        tester = TOMLExportTester()
        success = asyncio.run(tester.test_toml_format())
    elif args.mode == "api":
        tester = TOMLExportTester()
        success = tester.test_api_endpoints()
    elif args.mode == "all":
        tester = TOMLExportTester()
        
        tests = [
            ("Быстрый тест TOML", quick_toml_test()),
            ("TOML генератор", tester.test_toml_generation()),
            ("Логика экспорта", tester.test_export_logic()),
            ("Формат TOML", tester.test_toml_format()),
            ("API endpoints", asyncio.create_task(asyncio.coroutine(tester.test_api_endpoints)()))
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_task in tests:
            print(f"\n🔄 {test_name}...")
            try:
                if test_name == "API endpoints":
                    # Синхронный тест
                    result = tester.test_api_endpoints()
                else:
                    # Асинхронный тест
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
        print("\n🎉 Тестирование TOML Export завершено успешно!")
        
        if args.mode == "quick":
            print("\nДля полного тестирования:")
            print("   python3 scripts/test_toml_export.py --mode all")
            print("\nДля тестирования с работающим сервером:")
            print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 (из папки backend)")
            print("   curl http://localhost:8000/config/dynamic_strategy.toml")
    else:
        print("\n❌ Тестирование TOML Export не удалось")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
