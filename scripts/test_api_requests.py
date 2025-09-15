#!/usr/bin/env python3
"""
Test API requests for ToTheMoon2
Примеры запросов к API для тестирования
"""

import json
import time
import requests
from typing import Dict, Any

# Базовый URL API
BASE_URL = "http://localhost:8000/api"
HEALTH_URL = "http://localhost:8000/health"

def test_health():
    """Тест health check"""
    print("🔍 Тестирование /health...")
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_info():
    """Тест info endpoint"""
    print("\n🔍 Тестирование /api/info...")
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_system_stats():
    """Тест системной статистики"""
    print("\n🔍 Тестирование /api/system/stats...")
    try:
        response = requests.get(f"{BASE_URL}/system/stats", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_system_config():
    """Тест системной конфигурации"""
    print("\n🔍 Тестирование /api/system/config...")
    try:
        response = requests.get(f"{BASE_URL}/system/config", timeout=5)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Config categories: {list(response_data.get('config', {}).keys())}")
        print(f"Total params: {response_data.get('total_params', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_get_tokens():
    """Тест получения списка токенов"""
    print("\n🔍 Тестирование GET /api/tokens...")
    try:
        response = requests.get(f"{BASE_URL}/tokens", timeout=5)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Total tokens: {response_data.get('total', 0)}")
        print(f"Tokens in response: {len(response_data.get('tokens', []))}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_create_token():
    """Тест создания токена"""
    print("\n🔍 Тестирование POST /api/tokens...")
    try:
        # Создаем тестовый токен
        test_token = {
            "token_address": "So11111111111111111111111111111111111111112"
        }
        
        response = requests.post(
            f"{BASE_URL}/tokens",
            json=test_token,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            token_data = response.json()
            print(f"Created token: {token_data.get('token_address')}")
            print(f"Token ID: {token_data.get('id')}")
            print(f"Status: {token_data.get('status')}")
            return True
        elif response.status_code == 400:
            print(f"Token already exists (expected): {response.json()}")
            return True  # Это нормально, если токен уже существует
        else:
            print(f"Error response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_get_pools():
    """Тест получения списка пулов"""
    print("\n🔍 Тестирование GET /api/pools...")
    try:
        response = requests.get(f"{BASE_URL}/pools", timeout=5)
        print(f"Status: {response.status_code}")
        pools = response.json()
        print(f"Total pools: {len(pools)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_api_docs():
    """Тест доступности API документации"""
    print("\n🔍 Тестирование /api/docs...")
    try:
        response = requests.get("http://localhost:8000/api/docs", timeout=5)
        print(f"Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Главная функция тестирования API"""
    print("🧪 ТЕСТИРОВАНИЕ API ENDPOINTS")
    print("=" * 50)
    print("Убедитесь, что backend запущен (uvicorn) и доступен по http://localhost:8000")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("App Info", test_info),
        ("System Stats", test_system_stats),
        ("System Config", test_system_config),
        ("Get Tokens", test_get_tokens),
        ("Create Token", test_create_token),
        ("Get Pools", test_get_pools),
        ("API Docs", test_api_docs),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print("✅ Прошел")
            else:
                failed += 1
                print("❌ Не прошел")
        except Exception as e:
            failed += 1
            print(f"❌ Исключение: {e}")
        
        time.sleep(0.5)  # Небольшая пауза между запросами
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed} прошло, {failed} не прошло")
    
    if failed == 0:
        print("🎉 ВСЕ API ENDPOINTS РАБОТАЮТ!")
        print("\n📚 Документация доступна на: http://localhost/api/docs")
        print("🔧 Интерактивное тестирование: http://localhost/api/redoc")
    else:
        print("❌ Есть проблемы с API endpoints")
        print("📋 Проверьте логи backend (uvicorn) и Celery")

if __name__ == "__main__":
    main()
