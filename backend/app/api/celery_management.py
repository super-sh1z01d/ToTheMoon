"""
Celery management and monitoring endpoints
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.celery_monitoring.monitor import celery_monitor
from app.core.celery_monitoring.health import celery_health_checker

router = APIRouter(prefix="/celery", tags=["celery"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_celery_status() -> Dict[str, Any]:
    """
    Получить общий статус Celery системы
    """
    try:
        comprehensive_status = await celery_monitor.get_comprehensive_status()
        return comprehensive_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get Celery status", "details": {"error": str(e)}})


@router.get("/workers")
async def get_workers_status() -> Dict[str, Any]:
    """
    Получить статус всех Celery workers
    """
    try:
        workers_status = await celery_monitor.get_workers_status()
        return workers_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get workers status", "details": {"error": str(e)}})


@router.get("/queues")
async def get_queues_status() -> Dict[str, Any]:
    """
    Получить статус очередей Celery
    """
    try:
        queue_status = await celery_monitor.get_queue_status()
        redis_stats = await celery_monitor.get_redis_queue_stats()
        
        return {
            "queues": queue_status,
            "redis_details": redis_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get queues status", "details": {"error": str(e)}})


@router.get("/tasks")
async def get_tasks_stats(
    hours_back: int = Query(1, ge=1, le=24, description="Часов назад для истории задач")
) -> Dict[str, Any]:
    """
    Получить статистику выполнения задач
    """
    try:
        tasks_stats = await celery_monitor.get_tasks_stats()
        task_history = await celery_monitor.get_task_history(hours_back=hours_back)
        
        return {
            "current_tasks": tasks_stats,
            "task_history": task_history,
            "period_hours": hours_back,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get tasks stats", "details": {"error": str(e)}})


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Получить метрики производительности Celery workers
    """
    try:
        performance_metrics = await celery_monitor.get_performance_metrics()
        return performance_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get performance metrics", "details": {"error": str(e)}})


@router.get("/beat")
async def get_beat_scheduler_status() -> Dict[str, Any]:
    """
    Получить статус планировщика Beat
    """
    try:
        beat_status = await celery_monitor.check_beat_scheduler()
        return beat_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get beat scheduler status", "details": {"error": str(e)}})


@router.post("/health-check")
async def run_health_check(
    timeout: float = Query(10.0, ge=1.0, le=60.0, description="Таймаут проверки в секундах")
) -> Dict[str, Any]:
    """
    Запустить комплексную проверку здоровья Celery системы
    """
    try:
        health_result = await celery_health_checker.run_comprehensive_health_check()
        return health_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to run health check", "details": {"error": str(e)}})


@router.get("/health-history")
async def get_health_history(
    hours_back: int = Query(24, ge=1, le=168, description="Часов назад для истории")
) -> Dict[str, Any]:
    """
    Получить историю health checks
    """
    try:
        history = celery_health_checker.get_health_history(hours_back=hours_back)
        
        return {
            "health_history": history,
            "period_hours": hours_back,
            "total_records": len(history),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get health history", "details": {"error": str(e)}})


@router.post("/ping-workers")
async def ping_workers(
    timeout: float = Query(5.0, ge=1.0, le=30.0, description="Таймаут ping в секундах")
) -> Dict[str, Any]:
    """
    Ping всех активных workers
    """
    try:
        ping_result = await celery_health_checker.ping_workers(timeout=timeout)
        return ping_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to ping workers", "details": {"error": str(e)}})


@router.post("/test-task")
async def run_test_task() -> Dict[str, Any]:
    """
    Запустить тестовую задачу для проверки работоспособности
    """
    try:
        from app.workers.celery_health_tasks import health_check_task
        
        # Запускаем health check задачу
        task = health_check_task.delay()
        
        return {
            "message": "Health check task initiated",
            "task_id": task.id,
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to run test task", "details": {"error": str(e)}})


@router.post("/stress-test")
async def run_stress_test(
    duration: int = Query(5, ge=1, le=30, description="Длительность теста в секундах"),
    memory_mb: int = Query(10, ge=1, le=100, description="Количество памяти для выделения"),
    cpu_intensive: bool = Query(False, description="Выполнять CPU-intensive операции")
) -> Dict[str, Any]:
    """
    Запустить стресс-тест workers
    """
    try:
        from app.workers.celery_health_tasks import stress_test_task
        
        # Запускаем стресс-тест
        task = stress_test_task.delay(
            duration_seconds=duration,
            memory_mb=memory_mb,
            cpu_intensive=cpu_intensive
        )
        
        return {
            "message": f"Stress test initiated: {duration}s, {memory_mb}MB, CPU: {cpu_intensive}",
            "task_id": task.id,
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to run stress test", "details": {"error": str(e)}})


@router.post("/diagnose")
async def diagnose_celery_issues() -> Dict[str, Any]:
    """
    Диагностика проблем Celery системы с рекомендациями
    """
    try:
        diagnosis = await celery_health_checker.diagnose_issues()
        return diagnosis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to diagnose issues", "details": {"error": str(e)}})


@router.get("/config")
async def get_celery_config() -> Dict[str, Any]:
    """
    Получить текущую конфигурацию Celery
    """
    try:
        from app.core.celery_app import celery_app
        
        # Собираем ключевые настройки конфигурации
        config_info = {
            "broker_url": celery_app.conf.broker_url,
            "result_backend": celery_app.conf.result_backend,
            "task_serializer": celery_app.conf.task_serializer,
            "result_serializer": celery_app.conf.result_serializer,
            "worker_concurrency": celery_app.conf.worker_concurrency,
            "worker_prefetch_multiplier": celery_app.conf.worker_prefetch_multiplier,
            "task_soft_time_limit": celery_app.conf.task_soft_time_limit,
            "task_time_limit": celery_app.conf.task_time_limit,
            "worker_proc_alive_timeout": celery_app.conf.worker_proc_alive_timeout,
        }
        
        # Статистика beat schedule
        beat_schedule = celery_app.conf.beat_schedule or {}
        
        return {
            "celery_config": config_info,
            "beat_schedule": {
                "total_scheduled_tasks": len(beat_schedule),
                "task_names": list(beat_schedule.keys())
            },
            "optimization_notes": {
                "memory_optimized_for": "2GB RAM VPS",
                "worker_concurrency": "Limited to 2 for resource constraints",
                "prefetch_multiplier": "Set to 1 to prevent memory hogging"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get Celery config", "details": {"error": str(e)}})


@router.post("/purge-queue")
async def purge_queue(
    queue_name: str = Query("celery", description="Название очереди для очистки"),
    confirm: bool = Query(False, description="Подтверждение очистки")
) -> Dict[str, Any]:
    """
    Очистка очереди Celery (опасная операция!)
    """
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail={"message": "Purge requires confirmation", "details": {"hint": "Add ?confirm=true"}})
        
        from app.core.celery_app import celery_app
        
        # Очищаем очередь
        purged_count = celery_app.control.purge()
        
        logger.warning(
            f"Celery queue '{queue_name}' purged",
            extra={
                "queue_name": queue_name,
                "purged_tasks": purged_count,
                "operation": "queue_purge"
            }
        )
        
        return {
            "message": f"Queue '{queue_name}' purged successfully",
            "purged_tasks": purged_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to purge queue", "details": {"error": str(e)}})


@router.get("/stats")
async def get_monitoring_stats() -> Dict[str, Any]:
    """
    Получить статистику системы мониторинга Celery
    """
    try:
        monitor_stats = celery_monitor.get_stats()
        
        return {
            "monitoring_stats": monitor_stats,
            "health_checks_available": True,
            "features": [
                "Workers monitoring",
                "Queue status tracking", 
                "Performance metrics",
                "Health checks",
                "Stress testing",
                "Configuration inspection"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get monitoring stats", "details": {"error": str(e)}})
