#!/usr/bin/env python3
"""
Migration utility for ToTheMoon2
Простая утилита для применения миграций Alembic
"""

import os
import sys
import subprocess
from pathlib import Path
from sqlalchemy import text

# Добавляем backend в путь
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))


def _load_env_from_dotenv():
    """
    Lightweight .env loader to populate os.environ before reading DATABASE_URL.
    Does not override variables already set in the environment.
    """
    env_path = project_root / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            if key and (key not in os.environ):
                os.environ[key] = val
    except Exception:
        # Не прерываем выполнение из‑за .env; просто идём дальше
        pass

def run_command(cmd: list[str], cwd: str = None) -> bool:
    """
    Выполнение команды с выводом результата
    """
    print(f"Выполняется: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Предупреждения: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения команды: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def check_database_connection() -> bool:
    """
    Проверка подключения к базе данных
    """
    try:
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Подключение к базе данных успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def main():
    """
    Главная функция для применения миграций
    """
    print("🚀 ToTheMoon2 Migration Tool")
    print("=" * 40)
    
    # Пытаемся загрузить переменные из .env (если не экспортированы)
    _load_env_from_dotenv()

    # Проверяем environment переменные
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL не установлен")
        print("Убедитесь, что .env файл настроен правильно")
        return False
    
    # Проверяем подключение к БД
    if not check_database_connection():
        return False
    
    backend_dir = str(backend_path)
    print(f"Рабочая директория: {backend_dir}")
    
    # Проверяем текущую ревизию
    print("\n📋 Проверка текущего состояния миграций:")
    if not run_command(["alembic", "current"], cwd=backend_dir):
        print("Возможно, это первый запуск миграций")
    
    # Применяем миграции
    print("\n⬆️ Применение миграций:")
    if not run_command(["alembic", "upgrade", "head"], cwd=backend_dir):
        print("❌ Ошибка применения миграций")
        return False
    
    # Показываем финальное состояние
    print("\n✅ Миграции применены успешно!")
    print("\n📋 Финальное состояние:")
    run_command(["alembic", "current"], cwd=backend_dir)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
