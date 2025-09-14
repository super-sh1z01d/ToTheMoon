#!/usr/bin/env python3
"""
Celery workers management utility
Утилита для управления Celery workers
"""

import os
import sys
import time
import signal
import subprocess
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class CeleryManager:
    """
    Менеджер для управления Celery workers
    """
    
    def __init__(self):
        self.backend_path = backend_path
        self.worker_processes: List[subprocess.Popen] = []
        self.beat_process: Optional[subprocess.Popen] = None
        
    def start_worker(self, worker_name: str = "worker1", concurrency: int = 2) -> bool:
        """
        Запуск Celery worker
        """
        try:
            print(f"🚀 Starting Celery worker '{worker_name}' with concurrency {concurrency}...")
            
            cmd = [
                "celery",
                "-A", "app.core.celery_app",
                "worker",
                f"--hostname={worker_name}@%h",
                f"--concurrency={concurrency}",
                "--loglevel=info",
                "--prefetch-multiplier=1",
                "--without-gossip",  # Экономия памяти
                "--without-mingle",  # Экономия памяти
                "--optimization=fair"  # Равномерное распределение задач
            ]
            
            # Запускаем worker
            process = subprocess.Popen(
                cmd,
                cwd=self.backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy()
            )
            
            self.worker_processes.append(process)
            
            print(f"✅ Worker '{worker_name}' started with PID {process.pid}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start worker '{worker_name}': {e}")
            return False
    
    def start_beat(self) -> bool:
        """
        Запуск Celery beat scheduler
        """
        try:
            print("⏰ Starting Celery beat scheduler...")
            
            cmd = [
                "celery",
                "-A", "app.core.celery_app",
                "beat",
                "--loglevel=info",
                "--pidfile=/tmp/celerybeat.pid",
                "--schedule=/tmp/celerybeat-schedule"
            ]
            
            # Запускаем beat
            self.beat_process = subprocess.Popen(
                cmd,
                cwd=self.backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy()
            )
            
            print(f"✅ Beat scheduler started with PID {self.beat_process.pid}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start beat scheduler: {e}")
            return False
    
    def stop_workers(self, graceful: bool = True, timeout: int = 30) -> bool:
        """
        Остановка всех workers
        """
        try:
            if not self.worker_processes:
                print("ℹ️  No workers running")
                return True
            
            print(f"🛑 Stopping {len(self.worker_processes)} workers (graceful={graceful})...")
            
            stopped_count = 0
            
            for i, process in enumerate(self.worker_processes):
                try:
                    if process.poll() is None:  # Процесс еще запущен
                        if graceful:
                            # Graceful shutdown
                            process.send_signal(signal.SIGTERM)
                            
                            # Ждем завершения
                            try:
                                process.wait(timeout=timeout)
                                print(f"✅ Worker {i+1} stopped gracefully")
                            except subprocess.TimeoutExpired:
                                print(f"⚠️  Worker {i+1} didn't stop gracefully, forcing...")
                                process.kill()
                                print(f"🔴 Worker {i+1} forcefully terminated")
                        else:
                            # Force shutdown
                            process.kill()
                            print(f"🔴 Worker {i+1} forcefully terminated")
                        
                        stopped_count += 1
                    else:
                        print(f"ℹ️  Worker {i+1} already stopped")
                        
                except Exception as e:
                    print(f"❌ Error stopping worker {i+1}: {e}")
            
            self.worker_processes.clear()
            
            print(f"✅ Stopped {stopped_count} workers")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop workers: {e}")
            return False
    
    def stop_beat(self, graceful: bool = True, timeout: int = 10) -> bool:
        """
        Остановка beat scheduler
        """
        try:
            if not self.beat_process:
                print("ℹ️  Beat scheduler not running")
                return True
            
            print("🛑 Stopping beat scheduler...")
            
            if self.beat_process.poll() is None:  # Процесс еще запущен
                if graceful:
                    self.beat_process.send_signal(signal.SIGTERM)
                    try:
                        self.beat_process.wait(timeout=timeout)
                        print("✅ Beat scheduler stopped gracefully")
                    except subprocess.TimeoutExpired:
                        print("⚠️  Beat scheduler didn't stop gracefully, forcing...")
                        self.beat_process.kill()
                        print("🔴 Beat scheduler forcefully terminated")
                else:
                    self.beat_process.kill()
                    print("🔴 Beat scheduler forcefully terminated")
            else:
                print("ℹ️  Beat scheduler already stopped")
            
            self.beat_process = None
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop beat scheduler: {e}")
            return False
    
    def restart_workers(self, concurrency: int = 2) -> bool:
        """
        Перезапуск всех workers
        """
        print("🔄 Restarting Celery workers...")
        
        # Останавливаем
        if not self.stop_workers(graceful=True, timeout=30):
            print("❌ Failed to stop workers for restart")
            return False
        
        # Ждем немного
        time.sleep(2)
        
        # Запускаем заново
        return self.start_worker("worker1", concurrency)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса управляемых процессов
        """
        status = {
            "workers": [],
            "beat_scheduler": None,
            "summary": {
                "total_workers": len(self.worker_processes),
                "running_workers": 0,
                "beat_running": False
            }
        }
        
        # Статус workers
        for i, process in enumerate(self.worker_processes):
            is_running = process.poll() is None
            
            if is_running:
                status["summary"]["running_workers"] += 1
            
            worker_status = {
                "name": f"worker{i+1}",
                "pid": process.pid,
                "running": is_running,
                "return_code": process.returncode if not is_running else None
            }
            
            # Дополнительная информация о процессе если доступна
            try:
                if is_running:
                    proc_info = psutil.Process(process.pid)
                    worker_status.update({
                        "cpu_percent": proc_info.cpu_percent(),
                        "memory_mb": round(proc_info.memory_info().rss / 1024 / 1024, 2),
                        "create_time": datetime.fromtimestamp(proc_info.create_time()).isoformat()
                    })
            except (psutil.NoSuchProcess, ImportError):
                pass
            
            status["workers"].append(worker_status)
        
        # Статус beat scheduler
        if self.beat_process:
            is_running = self.beat_process.poll() is None
            status["summary"]["beat_running"] = is_running
            
            beat_status = {
                "pid": self.beat_process.pid,
                "running": is_running,
                "return_code": self.beat_process.returncode if not is_running else None
            }
            
            # Дополнительная информация о beat процессе
            try:
                if is_running:
                    proc_info = psutil.Process(self.beat_process.pid)
                    beat_status.update({
                        "cpu_percent": proc_info.cpu_percent(),
                        "memory_mb": round(proc_info.memory_info().rss / 1024 / 1024, 2),
                        "create_time": datetime.fromtimestamp(proc_info.create_time()).isoformat()
                    })
            except (psutil.NoSuchProcess, ImportError):
                pass
            
            status["beat_scheduler"] = beat_status
        
        return status
    
    def cleanup(self):
        """
        Очистка всех процессов при завершении
        """
        print("🧹 Cleaning up Celery processes...")
        
        self.stop_workers(graceful=True, timeout=15)
        self.stop_beat(graceful=True, timeout=10)
        
        print("✅ Cleanup completed")


def run_production_mode():
    """
    Запуск в production режиме (оптимизировано под 2GB RAM)
    """
    print("🏭 PRODUCTION MODE - OPTIMIZED FOR 2GB RAM")
    print("=" * 50)
    
    manager = CeleryManager()
    
    def signal_handler(sig, frame):
        print("\n🛑 Received shutdown signal...")
        manager.cleanup()
        sys.exit(0)
    
    # Обработка сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Запускаем beat scheduler
        if not manager.start_beat():
            print("❌ Failed to start beat scheduler")
            return False
        
        # Запускаем один worker с concurrency=1 для экономии памяти
        if not manager.start_worker("production-worker", concurrency=1):
            print("❌ Failed to start worker")
            manager.cleanup()
            return False
        
        print("\n✅ Celery system started successfully!")
        print("📊 Monitoring available at:")
        print("   - /api/celery/status")
        print("   - /api/celery/workers") 
        print("   - /api/celery/performance")
        print("\n⚠️  Press Ctrl+C to stop gracefully")
        
        # Мониторинг в реальном времени
        while True:
            time.sleep(30)  # Проверяем каждые 30 секунд
            
            # Простая проверка что процессы запущены
            status = manager.get_status()
            
            running_workers = status["summary"]["running_workers"]
            beat_running = status["summary"]["beat_running"]
            
            if running_workers == 0:
                print("❌ All workers stopped, restarting...")
                manager.restart_workers(concurrency=1)
            
            if not beat_running:
                print("❌ Beat scheduler stopped, restarting...")
                manager.start_beat()
                
            print(f"📊 Status: {running_workers} workers, beat: {'✅' if beat_running else '❌'}")
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
        manager.cleanup()
        return True
    except Exception as e:
        print(f"❌ Production mode failed: {e}")
        manager.cleanup()
        return False


def run_development_mode():
    """
    Запуск в development режиме (для локальной разработки)
    """
    print("🔧 DEVELOPMENT MODE")
    print("=" * 30)
    
    manager = CeleryManager()
    
    def signal_handler(sig, frame):
        print("\n🛑 Development mode shutdown...")
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Запускаем beat
        manager.start_beat()
        
        # Запускаем worker с большим concurrency для разработки
        manager.start_worker("dev-worker", concurrency=2)
        
        print("\n✅ Development Celery started!")
        print("🔧 Для остановки: Ctrl+C")
        
        # Простой мониторинг
        while True:
            time.sleep(10)
            status = manager.get_status()
            print(f"📊 Workers: {status['summary']['running_workers']}, Beat: {'✅' if status['summary']['beat_running'] else '❌'}")
            
    except KeyboardInterrupt:
        print("\n🛑 Development mode stopped")
        manager.cleanup()
        return True
    except Exception as e:
        print(f"❌ Development mode failed: {e}")
        manager.cleanup()
        return False


def check_celery_status():
    """
    Проверка статуса Celery процессов
    """
    print("🔍 CHECKING CELERY STATUS")
    print("=" * 35)
    
    try:
        # Проверяем процессы через psutil
        celery_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                if 'celery' in ' '.join(proc.info['cmdline'] or []):
                    celery_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'type': 'worker' if 'worker' in ' '.join(proc.info['cmdline']) else 'beat',
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 2),
                        'cmdline': ' '.join(proc.info['cmdline'][:3])  # Первые 3 аргумента
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if celery_processes:
            print(f"✅ Found {len(celery_processes)} Celery processes:")
            
            total_memory = 0
            for proc in celery_processes:
                print(f"   {proc['type'].upper()}: PID {proc['pid']}, "
                     f"CPU: {proc['cpu_percent']:.1f}%, "
                     f"RAM: {proc['memory_mb']:.1f}MB")
                total_memory += proc['memory_mb']
            
            print(f"\n📊 Total memory usage: {total_memory:.1f}MB")
            print(f"📊 Memory usage of 2GB limit: {total_memory/2048*100:.1f}%")
            
            # Статус по типам
            workers = [p for p in celery_processes if p['type'] == 'worker']
            beats = [p for p in celery_processes if p['type'] == 'beat']
            
            print(f"\n📋 Summary:")
            print(f"   Workers: {len(workers)}")
            print(f"   Beat schedulers: {len(beats)}")
            
        else:
            print("❌ No Celery processes found")
            print("💡 Start Celery with: python3 scripts/start_celery.py worker|beat")
        
        return len(celery_processes) > 0
        
    except ImportError:
        print("⚠️  psutil not available, using basic check...")
        return True
    except Exception as e:
        print(f"❌ Failed to check status: {e}")
        return False


def kill_all_celery():
    """
    Принудительная остановка всех Celery процессов
    """
    print("💥 FORCE KILLING ALL CELERY PROCESSES")
    print("=" * 45)
    
    try:
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'celery' in ' '.join(proc.info['cmdline'] or []):
                    print(f"🔴 Killing PID {proc.info['pid']}: {proc.info['name']}")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed_count > 0:
            print(f"✅ Killed {killed_count} Celery processes")
        else:
            print("ℹ️  No Celery processes found to kill")
        
        return True
        
    except ImportError:
        print("⚠️  psutil not available for process killing")
        return False
    except Exception as e:
        print(f"❌ Failed to kill processes: {e}")
        return False


def main():
    """
    Главная функция управления Celery
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Celery Workers Management")
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status", "production", "development", "kill"],
        help="Command to execute"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Worker concurrency (default: 2)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of workers to start (default: 1)"
    )
    
    args = parser.parse_args()
    
    print("🔧 CELERY WORKERS MANAGER")
    print("=" * 40)
    
    if args.command == "status":
        success = check_celery_status()
    elif args.command == "kill":
        success = kill_all_celery()
    elif args.command == "production":
        success = run_production_mode()
    elif args.command == "development":
        success = run_development_mode()
    else:
        manager = CeleryManager()
        
        if args.command == "start":
            success = True
            # Запускаем beat
            if not manager.start_beat():
                success = False
            
            # Запускаем workers
            for i in range(args.workers):
                if not manager.start_worker(f"worker{i+1}", args.concurrency):
                    success = False
            
            if success:
                print(f"\n✅ Started {args.workers} workers with concurrency {args.concurrency}")
                print("ℹ️  Use 'status' command to monitor")
        
        elif args.command == "stop":
            success = manager.stop_workers() and manager.stop_beat()
        
        elif args.command == "restart":
            success = manager.restart_workers(args.concurrency)
            if success and not manager.beat_process:
                manager.start_beat()
    
    if success:
        print("\n🎉 Operation completed successfully!")
    else:
        print("\n❌ Operation failed!")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
