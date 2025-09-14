"""
Token lifecycle management endpoints
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.lifecycle.manager import lifecycle_manager
from app.crud import token_crud
from app.models.token import TokenStatus, StatusChangeReason
from app.workers.lifecycle_tasks import (
    monitor_initial_tokens_task,
    monitor_active_tokens_lifecycle_task,
    fetch_metrics_for_initial_tokens_task,
    force_token_status_change_task,
    get_lifecycle_stats_task
)

router = APIRouter(prefix="/lifecycle", tags=["lifecycle"])


@router.get("/status")
async def get_lifecycle_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получить статус lifecycle менеджера
    """
    try:
        # Статистика менеджера
        manager_stats = lifecycle_manager.get_stats()
        
        # Статистика токенов по статусам
        token_stats = token_crud.get_stats(db)
        
        # Конфигурация lifecycle параметров
        from app.crud import system_crud
        
        lifecycle_config = {}
        lifecycle_keys = [
            "MIN_LIQUIDITY_USD",
            "MIN_TX_COUNT",
            "ARCHIVAL_TIMEOUT_HOURS",
            "LOW_SCORE_HOURS",
            "LOW_ACTIVITY_CHECKS"
        ]
        
        for key in lifecycle_keys:
            config = system_crud.get_by_key(db, key=key)
            if config:
                lifecycle_config[key] = {
                    "value": config.value,
                    "description": config.description
                }
        
        return {
            "status": "configured",
            "manager_stats": manager_stats,
            "token_stats": token_stats,
            "lifecycle_config": lifecycle_config
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting lifecycle status", "details": {"error": str(e)}})


@router.post("/monitor-initial")
async def trigger_initial_monitoring():
    """
    Запустить мониторинг Initial токенов принудительно
    """
    try:
        task = monitor_initial_tokens_task.delay()
        
        return {
            "message": "Initial tokens monitoring initiated",
            "task_id": task.id,
            "status": "monitoring"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error starting Initial monitoring", "details": {"error": str(e)}})


@router.post("/monitor-active")
async def trigger_active_lifecycle_monitoring():
    """
    Запустить мониторинг жизненного цикла активных токенов
    """
    try:
        task = monitor_active_tokens_lifecycle_task.delay()
        
        return {
            "message": "Active tokens lifecycle monitoring initiated",
            "task_id": task.id,
            "status": "monitoring"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error starting Active monitoring", "details": {"error": str(e)}})


@router.post("/fetch-initial-metrics")
async def trigger_initial_metrics_fetch():
    """
    Запустить получение метрик для Initial токенов
    """
    try:
        task = fetch_metrics_for_initial_tokens_task.delay()
        
        return {
            "message": "Initial tokens metrics fetch initiated",
            "task_id": task.id,
            "status": "fetching"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error fetching Initial metrics", "details": {"error": str(e)}})


@router.post("/force-status-change")
async def force_token_status_change(
    token_address: str = Query(..., description="Адрес токена"),
    new_status: str = Query(..., description="Новый статус (initial, active, archived)"),
    reason: str = Query("manual", description="Причина изменения"),
    metadata: str = Query("Manual change via admin panel", description="Дополнительная информация")
):
    """
    Принудительное изменение статуса токена (для админки)
    """
    try:
        # Валидация статуса
        if new_status.lower() not in ["initial", "active", "archived"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid status",
                    "details": {
                        "given": new_status,
                        "allowed": ["initial", "active", "archived"],
                    },
                },
            )
        
        task = force_token_status_change_task.delay(
            token_address,
            new_status,
            reason,
            metadata
        )
        
        return {
            "message": f"Status change initiated for {token_address} -> {new_status}",
            "task_id": task.id,
            "status": "changing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error forcing status change", "details": {"error": str(e)}})


@router.get("/stats")
async def get_lifecycle_stats():
    """
    Получить статистику lifecycle
    """
    try:
        task = get_lifecycle_stats_task.delay()
        
        return {
            "message": "Lifecycle stats retrieval initiated",
            "task_id": task.id,
            "status": "fetching"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting lifecycle stats", "details": {"error": str(e)}})


@router.get("/transitions")
async def get_recent_transitions(
    hours_back: int = Query(24, ge=1, le=168, description="Часов назад"),
    limit: int = Query(50, ge=1, le=500, description="Максимум записей"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить последние переходы статусов
    """
    try:
        from app.models.token import TokenStatusHistory
        from sqlalchemy import desc, and_
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        transitions = db.query(TokenStatusHistory).filter(
            TokenStatusHistory.changed_at >= cutoff_time
        ).order_by(desc(TokenStatusHistory.changed_at)).limit(limit).all()
        
        transitions_data = []
        for transition in transitions:
            token = token_crud.get(db, id=transition.token_id)
            transitions_data.append({
                "id": str(transition.id),
                "token_id": str(transition.token_id),
                "token_address": token.token_address if token else "unknown",
                "old_status": transition.old_status.value if transition.old_status else None,
                "new_status": transition.new_status.value,
                "reason": transition.reason.value,
                "changed_at": transition.changed_at.isoformat(),
                "change_metadata": transition.change_metadata
            })
        
        return {
            "transitions": transitions_data,
            "total_found": len(transitions_data),
            "period_hours": hours_back,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/tokens-by-age")
async def get_tokens_by_age(
    status: str = Query("initial", description="Статус токенов для анализа"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить токены сгруппированные по возрасту в текущем статусе
    """
    try:
        # Валидация статуса
        try:
            token_status = TokenStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail={"message": "Invalid status", "details": {"given": status, "allowed": ["initial", "active", "archived"]}})
        
        tokens = token_crud.get_by_status(
            db,
            status=token_status,
            limit=1000
        )
        
        # Группируем по возрасту
        now = datetime.now()
        age_groups = {
            "< 1 hour": [],
            "1-6 hours": [],
            "6-24 hours": [],
            "> 24 hours": []
        }
        
        for token in tokens:
            # Вычисляем возраст в текущем статусе
            if token_status == TokenStatus.INITIAL:
                age_from = token.created_at.replace(tzinfo=None)
            elif token_status == TokenStatus.ACTIVE:
                age_from = token.activated_at.replace(tzinfo=None) if token.activated_at else token.created_at.replace(tzinfo=None)
            else:  # ARCHIVED
                age_from = token.archived_at.replace(tzinfo=None) if token.archived_at else token.created_at.replace(tzinfo=None)
            
            age_hours = (now - age_from).total_seconds() / 3600
            
            token_data = {
                "token_address": token.token_address,
                "age_hours": round(age_hours, 2),
                "created_at": token.created_at.isoformat(),
                "status_since": age_from.isoformat()
            }
            
            if age_hours < 1:
                age_groups["< 1 hour"].append(token_data)
            elif age_hours < 6:
                age_groups["1-6 hours"].append(token_data)
            elif age_hours < 24:
                age_groups["6-24 hours"].append(token_data)
            else:
                age_groups["> 24 hours"].append(token_data)
        
        return {
            "status": status,
            "total_tokens": len(tokens),
            "age_groups": age_groups,
            "group_counts": {k: len(v) for k, v in age_groups.items()},
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/config")
async def get_lifecycle_config(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получить конфигурацию lifecycle параметров
    """
    try:
        from app.crud import system_crud
        
        # Параметры lifecycle
        lifecycle_params = {}
        lifecycle_keys = [
            "MIN_LIQUIDITY_USD",
            "MIN_TX_COUNT", 
            "ARCHIVAL_TIMEOUT_HOURS",
            "LOW_SCORE_HOURS",
            "LOW_ACTIVITY_CHECKS"
        ]
        
        for key in lifecycle_keys:
            config = system_crud.get_by_key(db, key=key)
            if config:
                lifecycle_params[key] = {
                    "value": config.value,
                    "description": config.description,
                    "category": config.category,
                    "updated_at": config.updated_at.isoformat()
                }
        
        return {
            "lifecycle_config": lifecycle_params,
            "total_params": len(lifecycle_params)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.put("/config/{key}")
async def update_lifecycle_config(
    key: str,
    value: dict,  # {"value": new_value, "description": optional_description}
    db: Session = Depends(get_db)
):
    """
    Обновить параметр конфигурации lifecycle
    """
    try:
        # Разрешенные ключи для lifecycle
        allowed_keys = [
            "MIN_LIQUIDITY_USD",
            "MIN_TX_COUNT",
            "ARCHIVAL_TIMEOUT_HOURS", 
            "LOW_SCORE_HOURS",
            "LOW_ACTIVITY_CHECKS"
        ]
        
        if key not in allowed_keys:
            raise HTTPException(status_code=400, detail={"message": "Key not allowed", "details": {"key": key, "allowed": allowed_keys}})
        
        if "value" not in value:
            raise HTTPException(status_code=400, detail={"message": "Missing field", "details": {"missing": "value"}})
        
        # Валидация значений
        new_value = value["value"]
        description = value.get("description")
        
        # Проверяем что значения положительные
        if key in ["MIN_LIQUIDITY_USD", "MIN_TX_COUNT", "ARCHIVAL_TIMEOUT_HOURS", "LOW_SCORE_HOURS", "LOW_ACTIVITY_CHECKS"]:
            if float(new_value) <= 0:
                raise HTTPException(status_code=400, detail={"message": "Parameter must be positive", "details": {"key": key, "given": new_value}})
        
        # Дополнительные проверки
        if key == "ARCHIVAL_TIMEOUT_HOURS" and float(new_value) < 1:
            raise HTTPException(status_code=400, detail={"message": "ARCHIVAL_TIMEOUT_HOURS must be at least 1 hour", "details": {"given": new_value}})
        
        if key == "LOW_ACTIVITY_CHECKS" and int(new_value) < 3:
            raise HTTPException(status_code=400, detail={"message": "LOW_ACTIVITY_CHECKS must be at least 3", "details": {"given": new_value}})
        
        # Обновляем конфигурацию
        from app.crud import system_crud
        
        config = system_crud.update_by_key(
            db,
            key=key,
            value=new_value,
            description=description
        )
        
        if not config:
            raise HTTPException(status_code=404, detail={"message": "Config parameter not found", "details": {"key": key}})
        
        logger.info(f"Lifecycle config updated: {key} = {new_value}")
        
        return {
            "message": f"Lifecycle config '{key}' updated successfully",
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "updated_at": config.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})
