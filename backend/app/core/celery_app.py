"""
Celery application configuration
"""

import os
from celery import Celery

# Создание Celery приложения
celery_app = Celery(
    "tothemoon2",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=[
        "app.workers.websocket_tasks",
        "app.workers.birdeye_tasks",
        "app.workers.scoring_tasks",
        "app.workers.lifecycle_tasks",
        "app.workers.toml_tasks",
        "app.workers.celery_health_tasks",
        # Здесь будут другие worker модули в следующих итерациях
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    # Основные настройки
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Настройки для ограниченных ресурсов (2 GB RAM)
    worker_concurrency=1,  # Только 1 параллельная задача в production
    worker_prefetch_multiplier=1,  # Не набирать задачи впрок
    task_acks_late=True,  # Подтверждать выполнение после завершения
    worker_disable_rate_limits=False,
    worker_max_memory_per_child=100000,  # 100MB на процесс, затем перезапуск
    worker_max_tasks_per_child=1000,  # Перезапуск после 1000 задач для освобождения памяти
    
    # Таймауты
    task_soft_time_limit=300,  # 5 минут мягкий лимит
    task_time_limit=600,       # 10 минут жесткий лимит
    
    # Retry настройки
    task_default_retry_delay=60,  # 1 минута
    task_max_retries=3,
    
    # Beat schedule (планировщик задач)
    beat_schedule={
        # WebSocket мониторинг (каждые 30 секунд)
        "check-websocket-status": {
            "task": "get_pumpportal_stats",
            "schedule": 30.0,
        },
        
        # Birdeye метрики для активных токенов (каждые 2 минуты)
        "fetch-active-tokens-metrics": {
            "task": "fetch_metrics_for_active_tokens",
            "schedule": 120.0,  # 2 минуты
        },
        
        # Birdeye статистика (каждые 5 минут)
        "birdeye-stats": {
            "task": "get_birdeye_stats",
            "schedule": 300.0,  # 5 минут
        },
        
        # Очистка старых данных (ежедневно в 3:00)
        "cleanup-old-data": {
            "task": "cleanup_old_birdeye_data",
            "schedule": 86400.0,  # 24 часа
        },
        
        # Scoring задачи
        "calculate-active-tokens-scores": {
            "task": "calculate_scores_for_active_tokens",
            "schedule": 180.0,  # 3 минуты (после получения метрик)
        },
        
        # Статистика скоринга (каждые 10 минут)
        "scoring-stats": {
            "task": "get_scoring_stats",
            "schedule": 600.0,  # 10 минут
        },
        
        # LIFECYCLE ЗАДАЧИ
        # Мониторинг Initial токенов (каждые 10 минут)
        "monitor-initial-tokens": {
            "task": "monitor_initial_tokens",
            "schedule": 600.0,  # 10 минут
        },
        
        # Мониторинг жизненного цикла активных токенов (каждые 5 минут)
        "monitor-active-lifecycle": {
            "task": "monitor_active_tokens_lifecycle", 
            "schedule": 300.0,  # 5 минут
        },
        
        # Получение метрик для Initial токенов (каждые 10 минут)
        "fetch-initial-tokens-metrics": {
            "task": "fetch_metrics_for_initial_tokens",
            "schedule": 600.0,  # 10 минут
        },
        
        # Статистика lifecycle (каждые 15 минут)
        "lifecycle-stats": {
            "task": "get_lifecycle_stats",
            "schedule": 900.0,  # 15 минут
        },
        
        # TOML EXPORT ЗАДАЧИ
        # Генерация TOML конфигурации (каждые 5 минут)
        "generate-toml-config": {
            "task": "generate_toml_config",
            "schedule": 300.0,  # 5 минут
        },
        
        # Валидация TOML экспорта (каждые 30 минут)
        "validate-toml-export": {
            "task": "validate_toml_export",
            "schedule": 1800.0,  # 30 минут
        },
        
        # Статистика TOML экспорта (каждые 20 минут)
        "toml-export-stats": {
            "task": "get_toml_export_stats",
            "schedule": 1200.0,  # 20 минут
        },
        
        # CELERY МОНИТОРИНГ
        # Мониторинг Celery системы (каждые 2 минуты)
        "celery-system-monitoring": {
            "task": "celery_monitor_stats",
            "schedule": 120.0,  # 2 минуты
        },
        
        # Health check workers (каждые 10 минут)
        "celery-health-check": {
            "task": "health_check_task",
            "schedule": 600.0,  # 10 минут
        },
    },
    
    # Логирование
    worker_log_level="INFO",
    worker_hijack_root_logger=False,
)

# Настройка для graceful shutdown
celery_app.conf.worker_proc_alive_timeout = 60  # 1 минута на graceful shutdown
