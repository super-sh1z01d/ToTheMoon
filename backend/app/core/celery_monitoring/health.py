"""
Celery health checks
Проверки здоровья Celery workers и системы
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CeleryHealthChecker:
    """
    Проверки здоровья Celery системы
    
    Выполняет:
    - Ping workers
    - Проверку выполнения тестовых задач
    - Мониторинг памяти
    - Проверку связности компонентов
    """
    
    def __init__(self):
        self.health_history = []
        self.max_history = 100  # Храним последние 100 проверок
        
    async def ping_workers(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Ping всех активных workers
        """
        try:
            from app.core.celery_app import celery_app
            
            logger.debug("Pinging Celery workers...")
            
            # Используем inspect для ping
            inspect = celery_app.control.inspect(timeout=timeout)
            
            # Ping workers
            ping_results = inspect.ping() or {}
            
            workers_status = []
            healthy_count = 0
            
            for worker_name, ping_response in ping_results.items():
                is_healthy = ping_response.get("ok") == "pong"
                
                if is_healthy:
                    healthy_count += 1
                
                workers_status.append({
                    "worker_name": worker_name,
                    "status": "healthy" if is_healthy else "unhealthy",
                    "ping_response": ping_response,
                    "response_time_ms": None  # TODO: Измерять время ответа
                })
            
            overall_status = "healthy" if healthy_count == len(workers_status) else "degraded"
            
            return {
                "status": overall_status,
                "workers": workers_status,
                "summary": {
                    "total_workers": len(workers_status),
                    "healthy_workers": healthy_count,
                    "unhealthy_workers": len(workers_status) - healthy_count
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to ping workers: {e}")
            return {
                "status": "error",
                "error": str(e),
                "workers": []
            }

    async def run_health_task(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Запуск специальной health check задачи
        """
        try:
            from app.workers.celery_health_tasks import health_check_task
            
            logger.debug("Running health check task...")
            
            start_time = time.time()
            
            # Запускаем задачу с timeout
            result = health_check_task.apply_async()
            
            try:
                # Ждем результат с timeout
                task_result = result.get(timeout=timeout)
                execution_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "success",
                    "task_id": result.id,
                    "result": task_result,
                    "execution_time_ms": execution_time,
                    "worker_node": result.info.get("hostname") if hasattr(result, "info") else None,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "failed",
                    "task_id": result.id,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to run health task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def check_memory_usage(self) -> Dict[str, Any]:
        """
        Проверка использования памяти workers
        """
        try:
            from app.core.celery_app import celery_app
            
            inspect = celery_app.control.inspect()
            stats_data = inspect.stats() or {}
            
            memory_usage = []
            total_memory = 0
            warning_threshold = 150 * 1024 * 1024  # 150MB на worker
            critical_threshold = 200 * 1024 * 1024  # 200MB на worker
            
            for worker_name, worker_stats in stats_data.items():
                rusage = worker_stats.get("rusage", {})
                memory_kb = rusage.get("maxrss", 0)
                memory_bytes = memory_kb * 1024
                
                total_memory += memory_bytes
                
                # Определяем статус памяти
                if memory_bytes > critical_threshold:
                    memory_status = "critical"
                elif memory_bytes > warning_threshold:
                    memory_status = "warning"
                else:
                    memory_status = "healthy"
                
                memory_usage.append({
                    "worker_name": worker_name,
                    "memory_bytes": memory_bytes,
                    "memory_mb": round(memory_bytes / 1024 / 1024, 2),
                    "memory_status": memory_status,
                    "pool_size": worker_stats.get("pool", {}).get("max-concurrency", 0)
                })
            
            # Общий статус памяти
            total_memory_mb = total_memory / 1024 / 1024
            memory_limit_mb = 2048  # 2GB лимит VPS
            usage_percent = (total_memory_mb / memory_limit_mb) * 100
            
            overall_memory_status = "healthy"
            if usage_percent > 90:
                overall_memory_status = "critical"
            elif usage_percent > 75:
                overall_memory_status = "warning"
            
            return {
                "status": overall_memory_status,
                "workers": memory_usage,
                "summary": {
                    "total_memory_mb": round(total_memory_mb, 2),
                    "memory_limit_mb": memory_limit_mb,
                    "usage_percent": round(usage_percent, 2),
                    "workers_over_warning": len([w for w in memory_usage if w["memory_status"] in ["warning", "critical"]]),
                    "workers_critical": len([w for w in memory_usage if w["memory_status"] == "critical"])
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check memory usage: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Комплексная проверка здоровья Celery системы
        """
        try:
            logger.info("Running comprehensive Celery health check...")
            
            # Выполняем все проверки
            checks = {
                "workers_ping": await self.ping_workers(),
                "memory_usage": await self.check_memory_usage(),
                "health_task": await self.run_health_task(),
            }
            
            # Анализируем результаты
            overall_status = "healthy"
            critical_issues = []
            warnings = []
            
            # Анализ workers
            if checks["workers_ping"]["status"] == "error":
                overall_status = "critical"
                critical_issues.append("Workers ping failed")
            elif checks["workers_ping"]["summary"]["unhealthy_workers"] > 0:
                overall_status = "degraded"
                warnings.append(f"{checks['workers_ping']['summary']['unhealthy_workers']} unhealthy workers")
            
            # Анализ памяти
            if checks["memory_usage"]["status"] == "critical":
                overall_status = "critical"
                critical_issues.append("Critical memory usage")
            elif checks["memory_usage"]["status"] == "warning":
                if overall_status == "healthy":
                    overall_status = "degraded"
                warnings.append("High memory usage")
            
            # Анализ health task
            if checks["health_task"]["status"] == "error":
                overall_status = "critical"
                critical_issues.append("Health task execution failed")
            elif checks["health_task"]["status"] == "failed":
                if overall_status == "healthy":
                    overall_status = "degraded"
                warnings.append("Health task failed")
            
            # Сохраняем в историю
            health_record = {
                "timestamp": datetime.now(),
                "overall_status": overall_status,
                "critical_issues": critical_issues,
                "warnings": warnings,
                "checks_summary": {
                    "workers_healthy": checks["workers_ping"]["summary"]["healthy_workers"],
                    "memory_usage_percent": checks["memory_usage"]["summary"]["usage_percent"],
                    "health_task_success": checks["health_task"]["status"] == "success"
                }
            }
            
            self.health_history.append(health_record)
            
            # Ограничиваем размер истории
            if len(self.health_history) > self.max_history:
                self.health_history = self.health_history[-self.max_history:]
            
            return {
                "overall_status": overall_status,
                "critical_issues": critical_issues,
                "warnings": warnings,
                "detailed_checks": checks,
                "health_summary": health_record["checks_summary"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            return {
                "overall_status": "error",
                "critical_issues": [f"Health check system error: {str(e)}"],
                "warnings": [],
                "detailed_checks": {},
                "timestamp": datetime.now().isoformat()
            }

    def get_health_history(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Получение истории health checks
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            # Фильтруем историю по времени
            recent_history = [
                {
                    "timestamp": record["timestamp"].isoformat(),
                    "overall_status": record["overall_status"],
                    "critical_issues_count": len(record["critical_issues"]),
                    "warnings_count": len(record["warnings"]),
                    "checks_summary": record["checks_summary"]
                }
                for record in self.health_history
                if record["timestamp"] >= cutoff_time
            ]
            
            return recent_history
            
        except Exception as e:
            logger.error(f"Failed to get health history: {e}")
            return []

    async def diagnose_issues(self) -> Dict[str, Any]:
        """
        Диагностика проблем Celery системы
        """
        try:
            # Запускаем комплексную проверку
            health_check = await self.run_comprehensive_health_check()
            
            # Анализируем проблемы и предлагаем решения
            diagnosis = {
                "timestamp": datetime.now().isoformat(),
                "issues_found": [],
                "recommendations": []
            }
            
            # Анализ critical issues
            for issue in health_check.get("critical_issues", []):
                diagnosis["issues_found"].append({
                    "severity": "critical",
                    "description": issue,
                    "category": self._categorize_issue(issue)
                })
            
            # Анализ warnings
            for warning in health_check.get("warnings", []):
                diagnosis["issues_found"].append({
                    "severity": "warning", 
                    "description": warning,
                    "category": self._categorize_issue(warning)
                })
            
            # Генерируем рекомендации
            diagnosis["recommendations"] = self._generate_recommendations(diagnosis["issues_found"])
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"Failed to diagnose issues: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "issues_found": [],
                "recommendations": [],
                "error": str(e)
            }

    def _categorize_issue(self, issue_text: str) -> str:
        """
        Категоризация проблемы
        """
        if "worker" in issue_text.lower():
            return "workers"
        elif "memory" in issue_text.lower():
            return "memory"
        elif "queue" in issue_text.lower():
            return "queues"
        elif "redis" in issue_text.lower():
            return "redis"
        elif "task" in issue_text.lower():
            return "tasks"
        else:
            return "general"

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """
        Генерация рекомендаций на основе найденных проблем
        """
        recommendations = []
        
        # Анализ по категориям
        categories = {}
        for issue in issues:
            category = issue["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(issue)
        
        # Рекомендации по workers
        if "workers" in categories:
            critical_workers = [i for i in categories["workers"] if i["severity"] == "critical"]
            if critical_workers:
                recommendations.append("🚨 Критично: Перезапустите Celery workers (systemctl restart tothemoon2-celery-worker)")
            else:
                recommendations.append("⚠️ Проверьте логи workers: journalctl -u tothemoon2-celery-worker -f")
        
        # Рекомендации по памяти
        if "memory" in categories:
            memory_issues = categories["memory"]
            critical_memory = [i for i in memory_issues if i["severity"] == "critical"]
            
            if critical_memory:
                recommendations.append("🚨 Критично: Высокое потребление памяти - снизьте concurrency workers")
                recommendations.append("💡 Проверьте настройки: worker_concurrency=1, prefetch_multiplier=1")
            else:
                recommendations.append("⚠️ Мониторьте потребление памяти - приближается к лимиту 2GB")
        
        # Рекомендации по очередям
        if "queues" in categories:
            recommendations.append("📋 Очереди перегружены - увеличьте количество workers или снизьте частоту задач")
            recommendations.append("🔧 Проверьте beat_schedule в celery_app.py")
        
        # Рекомендации по Redis
        if "redis" in categories:
            recommendations.append("🔴 Проблемы с Redis - проверьте подключение и логи Redis (systemctl status redis-server)")
            recommendations.append("🔧 Проверьте CELERY_BROKER_URL и CELERY_RESULT_BACKEND")
        
        # Рекомендации по задачам
        if "tasks" in categories:
            recommendations.append("⚠️ Проблемы с выполнением задач - проверьте логи конкретных workers")
            recommendations.append("🔍 Используйте /api/celery/tasks для анализа неудачных задач")
        
        # Общие рекомендации если нет проблем
        if not issues:
            recommendations.append("✅ Система здорова - все компоненты работают нормально")
            recommendations.append("📊 Рекомендуется регулярно мониторить через /api/celery/status")
        
        return recommendations


# Глобальный экземпляр health checker
celery_health_checker = CeleryHealthChecker()
