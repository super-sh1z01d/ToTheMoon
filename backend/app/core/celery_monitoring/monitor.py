"""
Celery workers monitoring
Мониторинг Celery воркеров и очередей
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CeleryMonitor:
    """
    Монитор для Celery workers и задач
    
    Отслеживает:
    - Состояние workers
    - Очереди задач
    - Производительность
    - Ошибки и таймауты
    """
    
    def __init__(self):
        self.stats = {
            "monitoring_started": None,
            "workers_checked": 0,
            "active_workers": 0,
            "failed_workers": 0,
            "total_tasks_processed": 0,
            "failed_tasks": 0,
            "last_check": None,
            "errors": 0
        }
        self._celery_app = None

    def _get_celery_app(self):
        """Получение Celery приложения"""
        if self._celery_app is None:
            try:
                from app.core.celery_app import celery_app
                self._celery_app = celery_app
            except Exception as e:
                logger.error(f"Failed to get Celery app: {e}")
                return None
        return self._celery_app

    async def get_workers_status(self) -> Dict[str, Any]:
        """
        Получение статуса всех Celery workers
        """
        try:
            celery_app = self._get_celery_app()
            if not celery_app:
                return {
                    "status": "error",
                    "error": "Celery app not available",
                    "workers": []
                }
            
            # Получаем статистику workers
            inspect = celery_app.control.inspect()
            
            # Активные workers
            active_workers = inspect.active() or {}
            stats_data = inspect.stats() or {}
            registered_tasks = inspect.registered() or {}
            
            workers_info = []
            active_count = 0
            
            for worker_name, worker_stats in stats_data.items():
                is_active = worker_name in active_workers
                
                if is_active:
                    active_count += 1
                
                # Информация о worker
                worker_info = {
                    "name": worker_name,
                    "status": "active" if is_active else "inactive",
                    "pool": worker_stats.get("pool", {}),
                    "total_tasks": len(active_workers.get(worker_name, [])),
                    "registered_tasks": len(registered_tasks.get(worker_name, [])),
                    "uptime": worker_stats.get("uptime", 0),
                    "load_avg": worker_stats.get("rusage", {}).get("utime", 0)
                }
                
                workers_info.append(worker_info)
            
            self.stats["workers_checked"] = len(workers_info)
            self.stats["active_workers"] = active_count
            self.stats["last_check"] = datetime.now()
            
            return {
                "status": "success",
                "workers": workers_info,
                "summary": {
                    "total_workers": len(workers_info),
                    "active_workers": active_count,
                    "inactive_workers": len(workers_info) - active_count
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get workers status: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "error": str(e),
                "workers": []
            }

    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Получение статуса очередей Celery
        """
        try:
            celery_app = self._get_celery_app()
            if not celery_app:
                return {
                    "status": "error",
                    "error": "Celery app not available",
                    "queues": []
                }
            
            # Используем Redis для проверки очередей
            import redis
            import os
            
            redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
            redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Получаем информацию об очередях
            queue_info = []
            
            # Основные очереди Celery
            default_queues = ["celery"]  # По умолчанию Celery использует 'celery' очередь
            
            for queue_name in default_queues:
                try:
                    # Длина очереди
                    queue_length = redis_client.llen(queue_name)
                    
                    queue_info.append({
                        "name": queue_name,
                        "length": queue_length,
                        "status": "healthy" if queue_length < 100 else "overloaded"
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to check queue {queue_name}: {e}")
                    queue_info.append({
                        "name": queue_name,
                        "length": -1,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "queues": queue_info,
                "summary": {
                    "total_queues": len(queue_info),
                    "healthy_queues": len([q for q in queue_info if q["status"] == "healthy"]),
                    "overloaded_queues": len([q for q in queue_info if q["status"] == "overloaded"])
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "error": str(e),
                "queues": []
            }

    async def get_tasks_stats(self) -> Dict[str, Any]:
        """
        Получение статистики выполненных задач
        """
        try:
            celery_app = self._get_celery_app()
            if not celery_app:
                return {
                    "status": "error", 
                    "error": "Celery app not available",
                    "tasks": {}
                }
            
            # Получаем статистику задач
            inspect = celery_app.control.inspect()
            
            # Активные задачи
            active_tasks = inspect.active() or {}
            # Зарезервированные задачи  
            reserved_tasks = inspect.reserved() or {}
            # Статистика выполненных задач
            stats_data = inspect.stats() or {}
            
            # Агрегируем данные
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())
            
            # Статистика по типам задач
            task_types = {}
            for worker_name, tasks in active_tasks.items():
                for task in tasks:
                    task_name = task.get("name", "unknown")
                    if task_name not in task_types:
                        task_types[task_name] = {
                            "active": 0,
                            "reserved": 0
                        }
                    task_types[task_name]["active"] += 1
            
            for worker_name, tasks in reserved_tasks.items():
                for task in tasks:
                    task_name = task.get("name", "unknown")
                    if task_name not in task_types:
                        task_types[task_name] = {
                            "active": 0,
                            "reserved": 0
                        }
                    task_types[task_name]["reserved"] += 1
            
            return {
                "status": "success",
                "summary": {
                    "total_active_tasks": total_active,
                    "total_reserved_tasks": total_reserved,
                    "total_workers_with_tasks": len(active_tasks),
                    "task_types_count": len(task_types)
                },
                "task_types": task_types,
                "active_tasks": active_tasks,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get tasks stats: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "error": str(e),
                "tasks": {}
            }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик производительности Celery
        """
        try:
            celery_app = self._get_celery_app()
            if not celery_app:
                return {
                    "status": "error",
                    "error": "Celery app not available"
                }
            
            inspect = celery_app.control.inspect()
            
            # Статистика workers
            stats_data = inspect.stats() or {}
            
            # Агрегируем метрики производительности
            total_completed = 0
            total_memory_usage = 0
            workers_count = 0
            
            performance_data = []
            
            for worker_name, worker_stats in stats_data.items():
                workers_count += 1
                
                rusage = worker_stats.get("rusage", {})
                pool_info = worker_stats.get("pool", {})
                
                completed_tasks = worker_stats.get("total", {})
                worker_completed = sum(completed_tasks.values()) if isinstance(completed_tasks, dict) else 0
                total_completed += worker_completed
                
                # Приблизительное использование памяти (если доступно)
                memory_usage = rusage.get("maxrss", 0)  # В KB на Linux
                total_memory_usage += memory_usage
                
                worker_performance = {
                    "worker_name": worker_name,
                    "completed_tasks": worker_completed,
                    "memory_usage_kb": memory_usage,
                    "cpu_time": rusage.get("utime", 0),
                    "pool_processes": pool_info.get("processes", 0),
                    "uptime": worker_stats.get("uptime", 0)
                }
                
                performance_data.append(worker_performance)
            
            # Общие метрики
            avg_memory = total_memory_usage / workers_count if workers_count > 0 else 0
            
            return {
                "status": "success",
                "summary": {
                    "total_workers": workers_count,
                    "total_completed_tasks": total_completed,
                    "total_memory_usage_mb": round(total_memory_usage / 1024, 2),  # Конвертируем в MB
                    "average_memory_per_worker_mb": round(avg_memory / 1024, 2),
                    "memory_limit_2gb_usage_percent": round((total_memory_usage / 1024) / 2048 * 100, 2)
                },
                "workers": performance_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "error": str(e)
            }

    async def check_beat_scheduler(self) -> Dict[str, Any]:
        """
        Проверка состояния планировщика Beat
        """
        try:
            celery_app = self._get_celery_app()
            if not celery_app:
                return {
                    "status": "error",
                    "error": "Celery app not available"
                }
            
            # Получаем конфигурацию beat schedule
            beat_schedule = celery_app.conf.beat_schedule or {}
            
            # Анализируем задачи планировщика
            scheduled_tasks = []
            total_tasks = len(beat_schedule)
            
            for task_name, task_config in beat_schedule.items():
                task_info = {
                    "name": task_name,
                    "task": task_config.get("task"),
                    "schedule": task_config.get("schedule"),
                    "enabled": True,  # По умолчанию все задачи включены
                    "last_run": None  # TODO: Получать из Redis если нужно
                }
                
                # Конвертируем schedule в читаемый формат
                schedule = task_config.get("schedule")
                if isinstance(schedule, (int, float)):
                    if schedule >= 3600:
                        task_info["schedule_human"] = f"{schedule/3600:.1f} часов"
                    elif schedule >= 60:
                        task_info["schedule_human"] = f"{schedule/60:.1f} минут"
                    else:
                        task_info["schedule_human"] = f"{schedule} секунд"
                else:
                    task_info["schedule_human"] = str(schedule)
                
                scheduled_tasks.append(task_info)
            
            return {
                "status": "success",
                "beat_scheduler": {
                    "total_scheduled_tasks": total_tasks,
                    "tasks": scheduled_tasks
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check beat scheduler: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_redis_queue_stats(self) -> Dict[str, Any]:
        """
        Получение детальной статистики Redis очередей
        """
        try:
            import redis
            import os
            
            # Подключаемся к Redis broker
            broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
            redis_client = redis.from_url(broker_url, decode_responses=True)
            
            # Получаем информацию о Redis
            redis_info = redis_client.info()
            
            # Получаем размеры очередей
            queue_stats = {}
            
            # Проверяем основные ключи Celery в Redis
            celery_keys = redis_client.keys("celery*")
            unacked_keys = redis_client.keys("unacked*")
            
            # Детали по очередям
            for key in celery_keys[:10]:  # Ограничиваем до 10 ключей
                key_type = redis_client.type(key)
                if key_type == "list":
                    length = redis_client.llen(key)
                elif key_type == "set":
                    length = redis_client.scard(key)
                elif key_type == "zset":
                    length = redis_client.zcard(key)
                else:
                    length = 1
                
                queue_stats[key] = {
                    "type": key_type,
                    "length": length
                }
            
            # Статистика памяти Redis
            memory_used = redis_info.get("used_memory", 0)
            memory_human = redis_info.get("used_memory_human", "0B")
            
            return {
                "status": "success",
                "redis_info": {
                    "version": redis_info.get("redis_version"),
                    "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "memory_used_bytes": memory_used,
                    "memory_used_human": memory_human,
                    "memory_usage_percent": round(memory_used / (100 * 1024 * 1024) * 100, 2)  # Процент от 100MB лимита
                },
                "queue_details": queue_stats,
                "celery_keys_count": len(celery_keys),
                "unacked_keys_count": len(unacked_keys),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get Redis queue stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_task_history(self, hours_back: int = 1) -> Dict[str, Any]:
        """
        Получение истории выполнения задач
        """
        try:
            # Получаем результаты задач из Redis backend
            import redis
            import os
            
            result_backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
            redis_client = redis.from_url(result_backend_url, decode_responses=True)
            
            # Получаем ключи результатов
            result_keys = redis_client.keys("celery-task-meta-*")
            
            # Анализируем результаты
            task_results = []
            success_count = 0
            failure_count = 0
            
            for key in result_keys[:50]:  # Ограничиваем до 50 последних задач
                try:
                    result_data = redis_client.get(key)
                    if result_data:
                        import json
                        task_info = json.loads(result_data)
                        
                        task_id = key.replace("celery-task-meta-", "")
                        status = task_info.get("status", "UNKNOWN")
                        
                        if status == "SUCCESS":
                            success_count += 1
                        elif status in ["FAILURE", "RETRY", "REVOKED"]:
                            failure_count += 1
                        
                        task_results.append({
                            "task_id": task_id[:8] + "...",  # Сокращенный ID
                            "status": status,
                            "task_name": task_info.get("task", "unknown"),
                            "timestamp": task_info.get("date_done", "unknown")
                        })
                        
                except Exception as e:
                    logger.debug(f"Failed to parse task result {key}: {e}")
                    continue
            
            # Сортируем по времени (если доступно)
            task_results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {
                "status": "success",
                "summary": {
                    "total_task_results": len(task_results),
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "success_rate": round(success_count / len(task_results) * 100, 2) if task_results else 0
                },
                "recent_tasks": task_results[:20],  # Последние 20 задач
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get task history: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Получение полного статуса Celery системы
        """
        try:
            # Собираем всю информацию параллельно
            workers_status = await self.get_workers_status()
            queue_status = await self.get_queue_status()
            tasks_stats = await self.get_tasks_stats()
            beat_status = await self.check_beat_scheduler()
            redis_stats = await self.get_redis_queue_stats()
            
            # Определяем общее состояние системы
            overall_status = "healthy"
            issues = []
            
            # Проверяем workers
            if workers_status.get("status") == "error":
                overall_status = "degraded"
                issues.append("Workers monitoring failed")
            elif workers_status.get("summary", {}).get("active_workers", 0) == 0:
                overall_status = "critical"
                issues.append("No active workers")
            
            # Проверяем очереди
            if queue_status.get("status") == "error":
                overall_status = "degraded"
                issues.append("Queue monitoring failed")
            elif queue_status.get("summary", {}).get("overloaded_queues", 0) > 0:
                if overall_status == "healthy":
                    overall_status = "degraded"
                issues.append("Overloaded queues detected")
            
            # Проверяем Redis
            if redis_stats.get("status") == "error":
                overall_status = "degraded"
                issues.append("Redis connection failed")
            
            # Проверяем Beat scheduler
            if beat_status.get("status") == "error":
                overall_status = "degraded"
                issues.append("Beat scheduler check failed")
            
            return {
                "overall_status": overall_status,
                "issues": issues,
                "components": {
                    "workers": workers_status,
                    "queues": queue_status,
                    "tasks": tasks_stats,
                    "beat_scheduler": beat_status,
                    "redis": redis_stats
                },
                "monitoring_stats": self.stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive status: {e}")
            self.stats["errors"] += 1
            return {
                "overall_status": "error",
                "issues": [f"Monitoring system error: {str(e)}"],
                "components": {},
                "monitoring_stats": self.stats,
                "timestamp": datetime.now().isoformat()
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики монитора
        """
        return self.stats.copy()

    async def reset_stats(self):
        """
        Сброс статистики мониторинга
        """
        self.stats = {
            "monitoring_started": datetime.now(),
            "workers_checked": 0,
            "active_workers": 0,
            "failed_workers": 0,
            "total_tasks_processed": 0,
            "failed_tasks": 0,
            "last_check": None,
            "errors": 0
        }
        
        logger.info("Celery monitoring stats reset")


# Глобальный экземпляр монитора
celery_monitor = CeleryMonitor()
