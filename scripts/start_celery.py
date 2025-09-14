#!/usr/bin/env python3
"""
Celery worker startup script for ToTheMoon2
"""

import os
import sys
import subprocess
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def start_celery_worker():
    """
    Запуск Celery worker
    """
    print("🚀 Starting Celery Worker...")
    
    os.chdir(backend_path)
    
    # Команда для запуска worker
    cmd = [
        "celery", 
        "-A", "app.core.celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=2",  # Ограничение для 2 GB RAM
        "--prefetch-multiplier=1"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery worker failed: {e}")
        return False
    
    return True

def start_celery_beat():
    """
    Запуск Celery beat (планировщик)
    """
    print("⏰ Starting Celery Beat...")
    
    os.chdir(backend_path)
    
    # Команда для запуска beat
    cmd = [
        "celery",
        "-A", "app.core.celery_app", 
        "beat",
        "--loglevel=info"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Celery beat stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery beat failed: {e}")
        return False
    
    return True

def main():
    """
    Главная функция - выбор режима запуска
    """
    if len(sys.argv) < 2:
        print("Usage: python start_celery.py [worker|beat|both]")
        print("  worker - запустить только worker")
        print("  beat   - запустить только планировщик")
        print("  both   - запустить worker и beat параллельно")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "worker":
        start_celery_worker()
    elif mode == "beat":
        start_celery_beat()
    elif mode == "both":
        print("🚀 Starting Celery Worker & Beat...")
        print("Для production используйте отдельные процессы!")
        
        # В development можно запустить оба процесса
        # В production лучше запускать отдельно
        import multiprocessing
        
        # Запускаем beat в отдельном процессе
        beat_process = multiprocessing.Process(target=start_celery_beat)
        beat_process.start()
        
        try:
            # Запускаем worker в основном процессе
            start_celery_worker()
        finally:
            print("Stopping beat process...")
            beat_process.terminate()
            beat_process.join()
    else:
        print(f"❌ Unknown mode: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
