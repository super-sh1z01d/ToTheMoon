"""
Celery health check tasks
Специальные задачи для проверки здоровья системы
"""

import logging
import time
import os
from datetime import datetime
from typing import Dict, Any

from celery import Celery

logger = logging.getLogger(__name__)

# Создаем Celery app (будет переопределен в main celery config)
celery_app = Celery("celery_health_tasks")


@celery_app.task(bind=True, name="health_check_task")
def health_check_task(self) -> Dict[str, Any]:
    """
    Базовая health check задача для проверки работоспособности worker
    
    Выполняет:
    - Проверку подключения к БД
    - Проверку подключения к Redis
    - Проверку доступности файловой системы
    - Сбор базовой информации о системе
    """
    try:
        start_time = time.time()
        
        health_result = {
            "task_id": self.request.id,
            "worker_name": self.request.hostname,
            "started_at": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "healthy"
        }
        
        issues = []
        
        # 1. Проверка БД
        try:
            from app.database import SessionLocal
            
            if SessionLocal:
                db = SessionLocal()
                try:
                from sqlalchemy import text
                result = db.execute(text("SELECT 1 as health_check"))
                    row = result.fetchone()
                    
                    health_result["checks"]["database"] = {
                        "status": "healthy" if row[0] == 1 else "failed",
                        "response_time_ms": round((time.time() - start_time) * 1000, 2)
                    }
                    
                    if row[0] != 1:
                        issues.append("Database query returned unexpected result")
                        
                finally:
                    db.close()
            else:
                health_result["checks"]["database"] = {
                    "status": "not_configured",
                    "error": "DATABASE_URL not set"
                }
                issues.append("Database not configured")
                
        except Exception as e:
            health_result["checks"]["database"] = {
                "status": "failed",
                "error": str(e)
            }
            issues.append(f"Database check failed: {e}")
        
        # 2. Проверка Redis
        try:
            import redis
            
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Ping Redis
            ping_start = time.time()
            pong = redis_client.ping()
            ping_time = (time.time() - ping_start) * 1000
            
            health_result["checks"]["redis"] = {
                "status": "healthy" if pong else "failed",
                "response_time_ms": round(ping_time, 2)
            }
            
            if not pong:
                issues.append("Redis ping failed")
                
        except Exception as e:
            health_result["checks"]["redis"] = {
                "status": "failed",
                "error": str(e)
            }
            issues.append(f"Redis check failed: {e}")
        
        # 3. Проверка файловой системы
        try:
            import tempfile
            
            # Тест записи/чтения временного файла
            fs_start = time.time()
            
            with tempfile.NamedTemporaryFile(mode='w+', delete=True) as tmp_file:
                test_content = f"health_check_{datetime.now().timestamp()}"
                tmp_file.write(test_content)
                tmp_file.seek(0)
                read_content = tmp_file.read()
                
                fs_time = (time.time() - fs_start) * 1000
                
                health_result["checks"]["filesystem"] = {
                    "status": "healthy" if read_content == test_content else "failed",
                    "response_time_ms": round(fs_time, 2)
                }
                
                if read_content != test_content:
                    issues.append("Filesystem read/write test failed")
                    
        except Exception as e:
            health_result["checks"]["filesystem"] = {
                "status": "failed",
                "error": str(e)
            }
            issues.append(f"Filesystem check failed: {e}")
        
        # 4. Проверка системных ресурсов
        try:
            import psutil
            
            # CPU и память процесса
            process = psutil.Process()
            
            health_result["checks"]["system_resources"] = {
                "status": "healthy",
                "cpu_percent": process.cpu_percent(),
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "open_files": process.num_fds() if hasattr(process, 'num_fds') else None,
                "threads": process.num_threads()
            }
            
        except ImportError:
            # psutil не обязателен
            health_result["checks"]["system_resources"] = {
                "status": "not_available",
                "error": "psutil not installed"
            }
        except Exception as e:
            health_result["checks"]["system_resources"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Определяем общий статус
        if any("Database" in issue or "Redis" in issue for issue in issues):
            health_result["overall_status"] = "critical"
        elif issues:
            health_result["overall_status"] = "degraded"
        else:
            health_result["overall_status"] = "healthy"
        
        # Финальные данные
        execution_time = (time.time() - start_time) * 1000
        
        health_result.update({
            "completed_at": datetime.now().isoformat(),
            "execution_time_ms": round(execution_time, 2),
            "issues": issues,
            "checks_passed": len([c for c in health_result["checks"].values() if c.get("status") == "healthy"]),
            "total_checks": len(health_result["checks"])
        })
        
        logger.info(
            f"Health check completed: {health_result['overall_status']} "
            f"({health_result['checks_passed']}/{health_result['total_checks']} checks passed)",
            extra={
                "worker_name": health_result["worker_name"],
                "overall_status": health_result["overall_status"],
                "execution_time_ms": execution_time,
                "issues_count": len(issues)
            }
        )
        
        return health_result
        
    except Exception as e:
        logger.error(f"Health check task failed: {e}")
        return {
            "task_id": self.request.id if hasattr(self, 'request') else None,
            "worker_name": self.request.hostname if hasattr(self, 'request') else "unknown",
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(bind=True, name="stress_test_task")
def stress_test_task(
    self,
    duration_seconds: int = 5,
    memory_mb: int = 10,
    cpu_intensive: bool = False
) -> Dict[str, Any]:
    """
    Стресс-тест задача для проверки устойчивости workers
    
    Args:
        duration_seconds: Длительность теста
        memory_mb: Количество памяти для выделения
        cpu_intensive: Выполнять CPU-intensive операции
    """
    try:
        start_time = time.time()
        
        logger.info(f"Starting stress test: {duration_seconds}s, {memory_mb}MB, CPU: {cpu_intensive}")
        
        # Выделяем память
        memory_data = []
        if memory_mb > 0:
            try:
                # Выделяем память (примерно memory_mb МБ)
                chunk_size = 1024 * 1024  # 1MB chunks
                for _ in range(memory_mb):
                    memory_data.append(b'0' * chunk_size)
                    
                logger.debug(f"Allocated {memory_mb}MB memory")
            except MemoryError:
                logger.warning("Failed to allocate requested memory")
        
        # CPU intensive операции
        cpu_operations = 0
        if cpu_intensive:
            target_time = start_time + duration_seconds
            while time.time() < target_time:
                # Простые математические операции
                _ = sum(i * i for i in range(1000))
                cpu_operations += 1
                
                # Небольшая пауза чтобы не блокировать полностью
                if cpu_operations % 100 == 0:
                    time.sleep(0.001)
        else:
            # Просто ждем указанное время
            time.sleep(duration_seconds)
        
        execution_time = (time.time() - start_time) * 1000
        
        result = {
            "task_id": self.request.id,
            "worker_name": self.request.hostname,
            "test_config": {
                "duration_seconds": duration_seconds,
                "memory_mb": memory_mb,
                "cpu_intensive": cpu_intensive
            },
            "results": {
                "execution_time_ms": round(execution_time, 2),
                "memory_allocated_mb": len(memory_data),
                "cpu_operations": cpu_operations,
                "status": "completed"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"Stress test completed: {execution_time:.2f}ms",
            extra={
                "worker_name": result["worker_name"],
                "duration": duration_seconds,
                "memory_mb": memory_mb,
                "cpu_operations": cpu_operations
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Stress test task failed: {e}")
        return {
            "task_id": self.request.id if hasattr(self, 'request') else None,
            "worker_name": self.request.hostname if hasattr(self, 'request') else "unknown",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(name="celery_monitor_stats")
def celery_monitor_stats_task() -> Dict[str, Any]:
    """
    Task для сбора статистики мониторинга Celery
    
    Выполняется периодически для сбора метрик
    """
    try:
        from app.core.celery_monitoring.monitor import celery_monitor
        
        # Получаем комплексный статус
        # Поскольку это sync task, создаем event loop
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            comprehensive_status = loop.run_until_complete(
                celery_monitor.get_comprehensive_status()
            )
            
            logger.info(
                f"Celery monitoring: {comprehensive_status['overall_status']}",
                extra={
                    "overall_status": comprehensive_status["overall_status"],
                    "critical_issues": len(comprehensive_status.get("critical_issues", [])),
                    "warnings": len(comprehensive_status.get("warnings", [])),
                    "operation": "celery_monitoring"
                }
            )
            
            return comprehensive_status
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Celery monitor stats task failed: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(bind=True, name="worker_restart_test")
def worker_restart_test_task(self) -> Dict[str, Any]:
    """
    Тест устойчивости worker к перезапускам
    
    Имитирует различные сценарии нагрузки для проверки graceful shutdown
    """
    try:
        start_time = time.time()
        
        logger.info("Running worker restart test...")
        
        # Имитируем длительную задачу с периодическими проверками
        test_duration = 30  # 30 секунд
        check_interval = 1  # Проверяем каждую секунду
        
        checks_completed = 0
        target_time = start_time + test_duration
        
        while time.time() < target_time:
            # Проверяем, не получили ли сигнал остановки
            if self.is_aborted():
                logger.info("Worker restart test aborted gracefully")
                break
            
            # Простая операция для имитации работы
            _ = sum(i for i in range(1000))
            checks_completed += 1
            
            time.sleep(check_interval)
        
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "task_id": self.request.id,
            "worker_name": self.request.hostname,
            "test_result": {
                "status": "completed",
                "checks_completed": checks_completed,
                "execution_time_ms": round(execution_time, 2),
                "graceful_shutdown": self.is_aborted()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Worker restart test failed: {e}")
        return {
            "task_id": self.request.id if hasattr(self, 'request') else None,
            "worker_name": self.request.hostname if hasattr(self, 'request') else "unknown",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
