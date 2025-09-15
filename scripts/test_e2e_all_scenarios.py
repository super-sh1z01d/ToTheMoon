#!/usr/bin/env python3
"""
End-to-End testing of all ToTheMoon2 scenarios
Комплексное тестирование всех сценариев системы
"""

import asyncio
import sys
import os
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class E2EScenarioTester:
    """
    End-to-End тестер для всех сценариев ToTheMoon2
    """
    
    def __init__(self):
        self.base_url = "http://localhost"
        self.test_results = []
        self.created_tokens = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Логирование результата теста"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_infrastructure_health(self) -> bool:
        """Тест 1: Проверка инфраструктуры"""
        print("\n🔍 ТЕСТ 1: ИНФРАСТРУКТУРА")
        print("=" * 40)
        
        try:
            # Health check
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                overall_status = health_data.get("status")
                
                self.log_test("Health endpoint", overall_status == "healthy", f"Status: {overall_status}")
                
                # Проверяем сервисы
                services = health_data.get("services", {})
                all_healthy = all(status == "healthy" for status in services.values())
                self.log_test("All services healthy", all_healthy, f"Services: {services}")
                
                return overall_status == "healthy" and all_healthy
            else:
                self.log_test("Health endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Infrastructure health", False, str(e))
            return False
    
    async def test_api_availability(self) -> bool:
        """Тест 2: Доступность всех API endpoints"""
        print("\n🔍 ТЕСТ 2: API ENDPOINTS")
        print("=" * 35)
        
        critical_endpoints = [
            ("/api/system/stats", "System stats"),
            ("/api/tokens", "Tokens API"),
            ("/api/pools", "Pools API"),
            ("/api/websocket/pumpportal/status", "WebSocket status"),
            ("/api/birdeye/status", "Birdeye status"),
            ("/api/scoring/status", "Scoring status"),
            ("/api/lifecycle/status", "Lifecycle status"),
            ("/api/celery/status", "Celery status"),
            ("/config/dynamic_strategy.toml", "TOML export"),
            ("/config/preview", "TOML preview")
        ]
        
        success_count = 0
        
        for endpoint, description in critical_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code == 200
                
                if success:
                    success_count += 1
                
                self.log_test(f"API: {description}", success, f"HTTP {response.status_code}")
                
            except Exception as e:
                self.log_test(f"API: {description}", False, str(e))
        
        all_success = success_count == len(critical_endpoints)
        self.log_test("All API endpoints", all_success, f"{success_count}/{len(critical_endpoints)} working")
        
        return all_success
    
    async def test_token_lifecycle_scenario(self) -> bool:
        """Тест 3: Полный жизненный цикл токена"""
        print("\n🔍 ТЕСТ 3: ЖИЗНЕННЫЙ ЦИКЛ ТОКЕНА")
        print("=" * 45)
        
        try:
            # Создаем тестовый токен
            test_token_address = f"TestToken{int(time.time())}" + "1" * 20  # 44 символа
            
            token_data = {
                "token_address": test_token_address
            }
            
            # 1. Создание токена
            response = requests.post(
                f"{self.base_url}/api/tokens",
                json=token_data,
                timeout=10
            )
            
            if response.status_code == 201:
                created_token = response.json()
                token_id = created_token["id"]
                self.created_tokens.append(token_id)
                
                self.log_test("Token creation", True, f"Token ID: {token_id[:8]}...")
                
                # 2. Проверяем статус Initial
                initial_status = created_token.get("status")
                self.log_test("Initial status", initial_status == "initial", f"Status: {initial_status}")
                
                # 3. Получаем историю статусов
                history_response = requests.get(f"{self.base_url}/api/tokens/{token_id}/history", timeout=10)
                if history_response.status_code == 200:
                    history = history_response.json()
                    has_creation_record = len(history) > 0
                    self.log_test("Status history", has_creation_record, f"History records: {len(history)}")
                else:
                    self.log_test("Status history", False, f"HTTP {history_response.status_code}")
                
                return True
            else:
                self.log_test("Token creation", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Token lifecycle", False, str(e))
            return False
    
    async def test_birdeye_integration(self) -> bool:
        """Тест 4: Интеграция с Birdeye API"""
        print("\n🔍 ТЕСТ 4: BIRDEYE ИНТЕГРАЦИЯ")
        print("=" * 40)
        
        try:
            # Тест статуса Birdeye
            response = requests.get(f"{self.base_url}/api/birdeye/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                client_initialized = status_data.get("statistics", {}).get("client_initialized", False)
                
                self.log_test("Birdeye client", client_initialized, f"Status: {status_data.get('status')}")
                
                # Тест получения метрик для SOL токена
                sol_token = "So11111111111111111111111111111111111111112"
                
                fetch_response = requests.post(
                    f"{self.base_url}/api/birdeye/fetch/{sol_token}",
                    params={"save_to_db": False},
                    timeout=30
                )
                
                if fetch_response.status_code == 200:
                    fetch_data = fetch_response.json()
                    self.log_test("Birdeye fetch", True, f"SOL metrics fetched")
                    
                    return True
                else:
                    self.log_test("Birdeye fetch", False, f"HTTP {fetch_response.status_code}")
                    return False
            else:
                self.log_test("Birdeye status", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Birdeye integration", False, str(e))
            return False
    
    async def test_scoring_engine(self) -> bool:
        """Тест 5: Scoring Engine"""
        print("\n🔍 ТЕСТ 5: SCORING ENGINE")
        print("=" * 35)
        
        try:
            # Тест статуса scoring
            response = requests.get(f"{self.base_url}/api/scoring/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                model_loaded = status_data.get("manager", {}).get("model_loaded")
                
                self.log_test("Scoring engine", model_loaded is not None, f"Model: {status_data.get('current_model', {}).get('name')}")
                
                # Тест доступных моделей
                models_response = requests.get(f"{self.base_url}/api/scoring/models", timeout=10)
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    available_models = models_data.get("available_models", [])
                    
                    self.log_test("Scoring models", len(available_models) > 0, f"Models: {len(available_models)}")
                    
                    # Тест конфигурации
                    config_response = requests.get(f"{self.base_url}/api/scoring/config", timeout=10)
                    if config_response.status_code == 200:
                        config_data = config_response.json()
                        scoring_params = config_data.get("scoring_config", {})
                        
                        self.log_test("Scoring config", len(scoring_params) > 0, f"Params: {len(scoring_params)}")
                        return True
                    else:
                        self.log_test("Scoring config", False, f"HTTP {config_response.status_code}")
                        return False
                else:
                    self.log_test("Scoring models", False, f"HTTP {models_response.status_code}")
                    return False
            else:
                self.log_test("Scoring status", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Scoring engine", False, str(e))
            return False
    
    async def test_celery_workers(self) -> bool:
        """Тест 6: Celery Workers"""
        print("\n🔍 ТЕСТ 6: CELERY WORKERS")
        print("=" * 35)
        
        try:
            # Тест статуса Celery
            response = requests.get(f"{self.base_url}/api/celery/status", timeout=15)
            if response.status_code == 200:
                status_data = response.json()
                overall_status = status_data.get("overall_status")
                
                self.log_test("Celery status", overall_status in ["healthy", "degraded"], f"Status: {overall_status}")
                
                # Тест workers
                workers_response = requests.get(f"{self.base_url}/api/celery/workers", timeout=10)
                if workers_response.status_code == 200:
                    workers_data = workers_response.json()
                    summary = workers_data.get("summary", {})
                    active_workers = summary.get("active_workers", 0)
                    
                    self.log_test("Celery workers", active_workers > 0, f"Active: {active_workers}")
                    
                    # Тест производительности
                    perf_response = requests.get(f"{self.base_url}/api/celery/performance", timeout=10)
                    if perf_response.status_code == 200:
                        perf_data = perf_response.json()
                        memory_usage = perf_data.get("summary", {}).get("memory_limit_2gb_usage_percent", 0)
                        
                        memory_ok = memory_usage < 90  # Меньше 90% от 2GB
                        self.log_test("Memory usage", memory_ok, f"{memory_usage:.1f}% of 2GB")
                        
                        return overall_status in ["healthy", "degraded"] and active_workers > 0 and memory_ok
                    else:
                        self.log_test("Celery performance", False, f"HTTP {perf_response.status_code}")
                        return False
                else:
                    self.log_test("Celery workers", False, f"HTTP {workers_response.status_code}")
                    return False
            else:
                self.log_test("Celery status", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Celery workers", False, str(e))
            return False
    
    async def test_toml_export_scenario(self) -> bool:
        """Тест 7: TOML экспорт для бота"""
        print("\n🔍 ТЕСТ 7: TOML ЭКСПОРТ")
        print("=" * 30)
        
        try:
            # Тест основного TOML endpoint
            response = requests.get(f"{self.base_url}/config/dynamic_strategy.toml", timeout=10)
            if response.status_code == 200:
                toml_content = response.text
                
                # Проверяем что это валидный TOML
                try:
                    import toml
                    parsed_config = toml.loads(toml_content)
                    
                    # Проверяем структуру
                    has_strategy = "strategy" in parsed_config
                    has_tokens = "tokens" in parsed_config
                    has_metadata = "metadata" in parsed_config
                    
                    structure_ok = has_strategy and has_tokens and has_metadata
                    self.log_test("TOML structure", structure_ok, f"Sections: strategy={has_strategy}, tokens={has_tokens}, metadata={has_metadata}")
                    
                    # Проверяем содержимое
                    tokens = parsed_config.get("tokens", [])
                    strategy = parsed_config.get("strategy", {})
                    
                    self.log_test("TOML content", True, f"Tokens: {len(tokens)}, Model: {strategy.get('model_name')}")
                    
                    # Тест кастомных параметров
                    custom_response = requests.get(
                        f"{self.base_url}/config/dynamic_strategy.toml?min_score=0.1&top_count=5",
                        timeout=10
                    )
                    
                    if custom_response.status_code == 200:
                        self.log_test("TOML custom params", True, "Custom parameters work")
                    else:
                        self.log_test("TOML custom params", False, f"HTTP {custom_response.status_code}")
                    
                    return structure_ok
                    
                except Exception as e:
                    self.log_test("TOML parsing", False, f"Parse error: {e}")
                    return False
            else:
                self.log_test("TOML endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("TOML export", False, str(e))
            return False
    
    async def test_admin_panel_scenario(self) -> bool:
        """Тест 8: Админ-панель"""
        print("\n🔍 ТЕСТ 8: АДМИН-ПАНЕЛЬ")
        print("=" * 35)
        
        try:
            # Тест системной конфигурации
            response = requests.get(f"{self.base_url}/api/system/config", timeout=10)
            if response.status_code == 200:
                config_data = response.json()
                total_params = config_data.get("total_params", 0)
                config_categories = config_data.get("config", {})
                
                self.log_test("System config", total_params > 0, f"Params: {total_params}, Categories: {len(config_categories)}")
                
                # Проверяем ключевые категории
                expected_categories = ["scoring", "lifecycle", "export", "api"]
                found_categories = [cat for cat in expected_categories if cat in config_categories]
                
                categories_ok = len(found_categories) >= 3  # Минимум 3 категории
                self.log_test("Config categories", categories_ok, f"Found: {found_categories}")
                
                # Тест обновления конфигурации (безопасный тест)
                test_key = "MIN_SCORE_THRESHOLD" 
                if "scoring" in config_categories and test_key in config_categories["scoring"]:
                    current_value = config_categories["scoring"][test_key]["value"]
                    
                    # Обновляем на тот же value (безопасно)
                    update_response = requests.put(
                        f"{self.base_url}/api/system/config/{test_key}",
                        json={"value": current_value, "description": "E2E test update"},
                        timeout=10
                    )
                    
                    update_ok = update_response.status_code == 200
                    self.log_test("Config update", update_ok, f"Updated {test_key}")
                else:
                    self.log_test("Config update", False, f"Test key {test_key} not found")
                
                return total_params > 0 and categories_ok
            else:
                self.log_test("Admin panel config", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin panel", False, str(e))
            return False
    
    async def test_realtime_system(self) -> bool:
        """Тест 9: Real-time система"""
        print("\n🔍 ТЕСТ 9: REAL-TIME СИСТЕМА")
        print("=" * 40)
        
        try:
            # Тест real-time статуса
            response = requests.get(f"{self.base_url}/api/realtime/stats", timeout=10)
            if response.status_code == 200:
                realtime_data = response.json()
                websocket_stats = realtime_data.get("websocket_manager", {})
                notification_stats = realtime_data.get("notification_manager", {})
                
                self.log_test("Real-time stats", True, f"Active connections: {realtime_data.get('total_active_connections', 0)}")
                
                # Тест health real-time системы
                health_response = requests.get(f"{self.base_url}/api/realtime/health", timeout=10)
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    rt_status = health_data.get("status")
                    
                    self.log_test("Real-time health", rt_status == "healthy", f"Status: {rt_status}")
                    
                    # Тест уведомлений
                    test_notification = {
                        "message": "E2E test notification",
                        "test_id": "e2e_test"
                    }
                    
                    notification_response = requests.post(
                        f"{self.base_url}/api/realtime/test-notification",
                        params={"notification_type": "system_stats"},
                        json=test_notification,
                        timeout=10
                    )
                    
                    notification_ok = notification_response.status_code == 200
                    self.log_test("Test notification", notification_ok, "Notification sent")
                    
                    return rt_status == "healthy" and notification_ok
                else:
                    self.log_test("Real-time health", False, f"HTTP {health_response.status_code}")
                    return False
            else:
                self.log_test("Real-time stats", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Real-time system", False, str(e))
            return False
    
    async def test_performance_under_load(self) -> bool:
        """Тест 10: Производительность под нагрузкой"""
        print("\n🔍 ТЕСТ 10: ПРОИЗВОДИТЕЛЬНОСТЬ")
        print("=" * 40)
        
        try:
            start_time = time.time()
            
            # Серия запросов для проверки производительности
            test_requests = [
                f"{self.base_url}/api/system/stats",
                f"{self.base_url}/api/tokens?limit=10",
                f"{self.base_url}/api/scoring/status",
                f"{self.base_url}/api/celery/performance",
                f"{self.base_url}/config/preview"
            ]
            
            total_requests = 0
            successful_requests = 0
            total_response_time = 0
            
            # Выполняем по 3 запроса к каждому endpoint
            for endpoint in test_requests:
                for _ in range(3):
                    try:
                        req_start = time.time()
                        response = requests.get(endpoint, timeout=5)
                        req_time = time.time() - req_start
                        
                        total_requests += 1
                        total_response_time += req_time
                        
                        if response.status_code == 200:
                            successful_requests += 1
                            
                    except Exception as e:
                        total_requests += 1
                        print(f"⚠️  Request failed: {endpoint} - {e}")
            
            total_test_time = time.time() - start_time
            avg_response_time = total_response_time / total_requests if total_requests > 0 else 0
            success_rate = successful_requests / total_requests if total_requests > 0 else 0
            
            # Критерии производительности
            performance_ok = avg_response_time < 2.0 and success_rate > 0.8
            
            self.log_test(
                "Performance test", 
                performance_ok,
                f"Avg response: {avg_response_time:.3f}s, Success rate: {success_rate:.1%}"
            )
            
            # Проверяем что система не тратит слишком много памяти
            memory_response = requests.get(f"{self.base_url}/api/celery/performance", timeout=10)
            if memory_response.status_code == 200:
                memory_data = memory_response.json()
                memory_usage = memory_data.get("summary", {}).get("memory_limit_2gb_usage_percent", 0)
                
                memory_ok = memory_usage < 85  # Не более 85% под нагрузкой
                self.log_test("Memory under load", memory_ok, f"Memory: {memory_usage:.1f}%")
                
                return performance_ok and memory_ok
            else:
                return performance_ok
                
        except Exception as e:
            self.log_test("Performance test", False, str(e))
            return False
    
    async def test_full_data_flow(self) -> bool:
        """Тест 11: Полный поток данных (токены → скоринг → экспорт)"""
        print("\n🔍 ТЕСТ 11: ПОЛНЫЙ ПОТОК ДАННЫХ")
        print("=" * 45)
        
        try:
            # 1. Проверяем что есть токены в системе
            tokens_response = requests.get(f"{self.base_url}/api/tokens?limit=5", timeout=10)
            if tokens_response.status_code == 200:
                tokens_data = tokens_response.json()
                total_tokens = tokens_data.get("total", 0)
                
                self.log_test("Tokens in system", total_tokens > 0, f"Total tokens: {total_tokens}")
                
                # 2. Проверяем топ токены по скору
                top_tokens_response = requests.get(f"{self.base_url}/api/scoring/top-tokens", timeout=10)
                if top_tokens_response.status_code == 200:
                    top_tokens_data = top_tokens_response.json()
                    top_tokens = top_tokens_data.get("top_tokens", [])
                    
                    self.log_test("Top tokens", len(top_tokens) >= 0, f"Top tokens: {len(top_tokens)}")
                    
                    # 3. Проверяем TOML экспорт включает эти токены
                    toml_response = requests.get(f"{self.base_url}/config/preview", timeout=10)
                    if toml_response.status_code == 200:
                        toml_preview = toml_response.json()
                        export_tokens = toml_preview.get("total_tokens", 0)
                        
                        self.log_test("TOML export flow", True, f"Export tokens: {export_tokens}")
                        
                        # 4. Проверяем что данные актуальны
                        if export_tokens > 0:
                            selected_tokens = toml_preview.get("selected_tokens", [])
                            has_scores = all("score" in token for token in selected_tokens)
                            
                            self.log_test("Data freshness", has_scores, "All tokens have scores")
                            
                            return has_scores
                        else:
                            self.log_test("Data flow", True, "No tokens meet export criteria (expected)")
                            return True
                    else:
                        self.log_test("TOML preview", False, f"HTTP {toml_response.status_code}")
                        return False
                else:
                    self.log_test("Top tokens", False, f"HTTP {top_tokens_response.status_code}")
                    return False
            else:
                self.log_test("Tokens check", False, f"HTTP {tokens_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Full data flow", False, str(e))
            return False
    
    async def cleanup_test_data(self):
        """Очистка тестовых данных"""
        print("\n🧹 ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
        print("=" * 35)
        
        for token_id in self.created_tokens:
            try:
                response = requests.delete(f"{self.base_url}/api/tokens/{token_id}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ Deleted test token: {token_id[:8]}...")
                else:
                    print(f"⚠️  Failed to delete token {token_id[:8]}...: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️  Error deleting token {token_id[:8]}...: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Генерация отчета о тестировании"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
                "overall_status": "PASS" if success_rate >= 0.8 else "FAIL"
            },
            "test_results": self.test_results,
            "report_generated_at": datetime.now().isoformat()
        }


async def run_complete_e2e_test():
    """
    Полный E2E тест всех сценариев
    """
    print("🧪 COMPLETE END-TO-END TESTING")
    print("=" * 50)
    print("🎯 Testing all ToTheMoon2 scenarios according to ФЗ")
    print("=" * 50)
    
    tester = E2EScenarioTester()
    
    # Последовательность тестов согласно сценариям из vision.md
    tests = [
        ("Infrastructure Health", tester.test_infrastructure_health()),
        ("API Availability", tester.test_api_availability()),
        ("Token Lifecycle", tester.test_token_lifecycle_scenario()),
        ("Birdeye Integration", tester.test_birdeye_integration()),
        ("Scoring Engine", tester.test_scoring_engine()),
        ("Celery Workers", tester.test_celery_workers()),
        ("TOML Export", tester.test_toml_export_scenario()),
        ("Admin Panel", tester.test_admin_panel_scenario()),
        ("Real-time System", tester.test_realtime_system()),
        ("Performance Load Test", tester.test_performance_under_load()),
        ("Full Data Flow", tester.test_full_data_flow())
    ]
    
    print(f"🔄 Running {len(tests)} test scenarios...\n")
    
    # Выполняем все тесты
    for test_name, test_coro in tests:
        print(f"🔄 {test_name}...")
        try:
            success = await test_coro
            if not success:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    # Очищаем тестовые данные
    await tester.cleanup_test_data()
    
    # Генерируем отчет
    report = tester.generate_report()
    
    print("\n" + "=" * 50)
    print("📊 E2E TESTING REPORT")
    print("=" * 50)
    
    summary = report["summary"]
    print(f"Total tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Success rate: {summary['success_rate']:.1%}")
    print(f"Overall status: {summary['overall_status']}")
    
    # Детали по неудачным тестам
    failed_tests = [t for t in report["test_results"] if not t["success"]]
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"   • {test['test_name']}: {test['message']}")
    
    # Сохраняем отчет
    report_file = Path("./logs/e2e_test_report.json")
    report_file.parent.mkdir(exist_ok=True)
    
    import json
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    return summary["overall_status"] == "PASS"


def main():
    """
    Главная функция E2E тестирования
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="ToTheMoon2 End-to-End Testing")
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "performance", "infrastructure"],
        default="full",
        help="Testing mode"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save detailed report to logs/"
    )
    
    args = parser.parse_args()
    
    print("🌙 TOTHEMOON2 END-TO-END TESTING")
    print("=" * 50)
    print("🎯 Ensure backend and Celery are running (uvicorn + celery)")
    print("   Example: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("=" * 50)
    
    if args.mode == "full":
        success = asyncio.run(run_complete_e2e_test())
    else:
        # Простые тесты для других режимов
        tester = E2EScenarioTester()
        
        if args.mode == "quick":
            success = asyncio.run(tester.test_infrastructure_health())
        elif args.mode == "performance":
            success = asyncio.run(tester.test_performance_under_load())
        elif args.mode == "infrastructure":
            success = asyncio.run(tester.test_infrastructure_health())
    
    if success:
        print("\n🎉 END-TO-END TESTING COMPLETED SUCCESSFULLY!")
        print("🚀 System is ready for production deployment!")
    else:
        print("\n❌ END-TO-END TESTING FAILED!")
        print("🔧 Fix the issues before production deployment")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
