#!/usr/bin/env python3
"""
Test script for Iteration 4: React Frontend (MVP)
Тест готовности четвертой итерации
"""

import os
import json
from pathlib import Path

def test_project_structure():
    """Тест структуры React проекта"""
    print("🔍 Тестирование структуры проекта...")
    
    required_files = [
        "frontend/package.json",
        "frontend/tsconfig.json", 
        "frontend/vite.config.ts",
        "frontend/tailwind.config.js",
        "frontend/postcss.config.js",
        "frontend/index.html",
        "frontend/src/main.tsx",
        "frontend/src/App.tsx",
        "frontend/src/index.css"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Структура проекта корректна")
    return True

def test_package_json():
    """Тест package.json"""
    print("🔍 Тестирование package.json...")
    
    try:
        with open("frontend/package.json", "r") as f:
            package_data = json.load(f)
        
        required_deps = [
            "react", "react-dom", "react-query", 
            "recharts", "lucide-react"
        ]
        
        required_dev_deps = [
            "@types/react", "@types/react-dom", 
            "@vitejs/plugin-react", "typescript", 
            "tailwindcss", "vite"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if dep not in package_data.get("dependencies", {}):
                missing_deps.append(dep)
        
        for dep in required_dev_deps:
            if dep not in package_data.get("devDependencies", {}):
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Отсутствуют зависимости: {missing_deps}")
            return False
        
        # Проверяем scripts
        required_scripts = ["dev", "build", "preview"]
        for script in required_scripts:
            if script not in package_data.get("scripts", {}):
                print(f"❌ Отсутствует script: {script}")
                return False
        
        print("✅ package.json настроен корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка чтения package.json: {e}")
        return False

def test_typescript_config():
    """Тест TypeScript конфигурации"""
    print("🔍 Тестирование TypeScript конфигурации...")
    
    try:
        with open("frontend/tsconfig.json", "r") as f:
            tsconfig_data = json.load(f)
        
        # Проверяем ключевые настройки
        compiler_options = tsconfig_data.get("compilerOptions", {})
        
        required_options = {
            "target": "ES2020",
            "module": "ESNext",
            "jsx": "react-jsx",
            "strict": True
        }
        
        for option, expected_value in required_options.items():
            if compiler_options.get(option) != expected_value:
                print(f"❌ Неверная настройка TypeScript: {option} = {compiler_options.get(option)}, ожидается {expected_value}")
                return False
        
        print("✅ TypeScript конфигурация корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка чтения tsconfig.json: {e}")
        return False

def test_components():
    """Тест React компонентов"""
    print("🔍 Тестирование React компонентов...")
    
    required_components = [
        "frontend/src/components/Header.tsx",
        "frontend/src/components/SystemStats.tsx",
        "frontend/src/components/TokensTable.tsx",
        "frontend/src/components/TokensFilter.tsx",
        "frontend/src/components/TokenStatus.tsx",
        "frontend/src/components/AddressDisplay.tsx",
        "frontend/src/components/LoadingSkeleton.tsx"
    ]
    
    missing_components = []
    for component_path in required_components:
        if not os.path.exists(component_path):
            missing_components.append(component_path)
    
    if missing_components:
        print(f"❌ Отсутствуют компоненты: {missing_components}")
        return False
    
    print("✅ Все компоненты созданы")
    return True

def test_hooks_and_utils():
    """Тест хуков и утилит"""
    print("🔍 Тестирование хуков и утилит...")
    
    required_files = [
        "frontend/src/hooks/useApi.ts",
        "frontend/src/utils/api.ts",
        "frontend/src/utils/format.ts",
        "frontend/src/types/api.ts"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Хуки и утилиты созданы")
    return True

def test_tailwind_setup():
    """Тест настройки Tailwind CSS"""
    print("🔍 Тестирование Tailwind CSS...")
    
    # Проверяем tailwind.config.js
    if not os.path.exists("frontend/tailwind.config.js"):
        print("❌ Отсутствует tailwind.config.js")
        return False
    
    # Проверяем postcss.config.js
    if not os.path.exists("frontend/postcss.config.js"):
        print("❌ Отсутствует postcss.config.js")
        return False
    
    # Проверяем что в index.css есть Tailwind директивы
    try:
        with open("frontend/src/index.css", "r") as f:
            css_content = f.read()
        
        required_directives = ["@tailwind base", "@tailwind components", "@tailwind utilities"]
        for directive in required_directives:
            if directive not in css_content:
                print(f"❌ Отсутствует Tailwind директива: {directive}")
                return False
        
        print("✅ Tailwind CSS настроен корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка чтения index.css: {e}")
        return False

def test_pages():
    """Тест страниц"""
    print("🔍 Тестирование страниц...")
    
    required_pages = [
        "frontend/src/pages/HomePage.tsx"
    ]
    
    missing_pages = []
    for page_path in required_pages:
        if not os.path.exists(page_path):
            missing_pages.append(page_path)
    
    if missing_pages:
        print(f"❌ Отсутствуют страницы: {missing_pages}")
        return False
    
    print("✅ Страницы созданы")
    return True

def test_dev_setup():
    """Тест dev-настройки (без Docker)"""
    print("🔍 Тестирование dev-настройки...")
    
    try:
        # Проверяем, что API base URL настроен для dev
        with open("frontend/src/utils/api.ts", "r") as f:
            api_utils = f.read()
        
        if "VITE_API_BASE_URL" not in api_utils:
            print("❌ VITE_API_BASE_URL не используется в utils/api.ts")
            return False
        
        print("✅ Dev-настройка корректна (VITE_API_BASE_URL поддерживается)")
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки dev-настройки: {e}")
        return False

def test_import_syntax():
    """Тест синтаксиса импортов"""
    print("🔍 Тестирование синтаксиса импортов...")
    
    test_files = [
        "frontend/src/App.tsx",
        "frontend/src/main.tsx",
        "frontend/src/pages/HomePage.tsx",
        "frontend/src/components/Header.tsx"
    ]
    
    for file_path in test_files:
        try:
            with open(file_path, "r") as f:
                content = f.read()
            
            # Проверяем основные импорты React
            if file_path.endswith(".tsx") and "import React" not in content:
                print(f"❌ Отсутствует импорт React в {file_path}")
                return False
            
            # Проверяем типы TypeScript
            if "interface " not in content and "type " not in content and "React.FC" not in content:
                continue  # Может быть простой файл без типов
                
        except Exception as e:
            print(f"❌ Ошибка чтения {file_path}: {e}")
            return False
    
    print("✅ Синтаксис импортов корректен")
    return True

def main():
    """
    Главная функция тестирования
    """
    print("🧪 ТЕСТ ГОТОВНОСТИ ИТЕРАЦИИ 4")
    print("=" * 50)
    
    tests = [
        ("Структура проекта", test_project_structure),
        ("package.json", test_package_json),
        ("TypeScript конфигурация", test_typescript_config),
        ("React компоненты", test_components),
        ("Хуки и утилиты", test_hooks_and_utils),
        ("Tailwind CSS", test_tailwind_setup),
        ("Страницы", test_pages),
        ("Dev настройка", test_dev_setup),
        ("Синтаксис импортов", test_import_syntax),
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
        print("🎉 ИТЕРАЦИЯ 4 ГОТОВА К ТЕСТИРОВАНИЮ!")
        print("\nДля полного тестирования запустите:")
        print("1. npm run dev (в папке frontend)")
        print("2. Откройте http://localhost:3000")
        print("3. Проверьте работу интерфейса:")
        print("   - Отображение системной статистики")
        print("   - Таблица токенов")
        print("   - Фильтры по статусу")
        print("   - Responsive дизайн")
        print("4. Для production-сборки: npm run build (раздайте dist через Nginx)")
        return True
    else:
        print("❌ Есть проблемы, требующие исправления")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
