"""
Scoring engine management endpoints
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.scoring.manager import scoring_manager
from app.crud import token_crud, token_scores_crud
from app.workers.scoring_tasks import (
    calculate_token_score_task,
    calculate_scores_for_active_tokens_task,
    reload_scoring_model_task,
    test_scoring_model_task,
    get_scoring_stats_task
)

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.get("/status")
async def get_scoring_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получить статус scoring engine
    """
    try:
        # Статистика менеджера
        manager_stats = scoring_manager.get_stats()
        
        # Информация о модели
        model_info = await scoring_manager.get_model_info()
        
        # Доступные модели
        available_models = scoring_manager.get_available_models()
        
        # Последние скоры из БД
        latest_scores = db.query(token_scores_crud.model).order_by(
            token_scores_crud.model.calculated_at.desc()
        ).limit(5).all()
        
        latest_scores_data = []
        for score in latest_scores:
            latest_scores_data.append({
                "token_id": str(score.token_id),
                "model_name": score.model_name,
                "score_value": score.score_value,
                "calculated_at": score.calculated_at.isoformat()
            })
        
        return {
            "status": "configured" if manager_stats.get("model_loaded") else "not_configured",
            "manager": manager_stats,
            "current_model": model_info,
            "available_models": available_models,
            "latest_scores": latest_scores_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting scoring status", "details": {"error": str(e)}})


@router.post("/calculate/{token_address}")
async def calculate_token_score(
    token_address: str,
    async_mode: bool = Query(True, description="Асинхронный расчет через Celery")
) -> Dict[str, Any]:
    """
    Рассчитать скор для конкретного токена
    """
    try:
        if async_mode:
            # Запускаем через Celery task
            task = calculate_token_score_task.delay(token_address)
            
            return {
                "message": f"Score calculation initiated for {token_address}",
                "task_id": task.id,
                "status": "calculating"
            }
        else:
            # Прямой расчет (для тестирования)
            db = next(get_db())
            try:
                result = await scoring_manager.calculate_score_for_token(token_address, db)
                
                if result:
                    return {
                        "status": "success",
                        "token_address": token_address,
                        "score_value": result.score_value,
                        "score_smoothed": result.score_smoothed,
                        "model_name": result.model_name,
                        "components": result.components.to_dict(),
                        "execution_time_ms": result.execution_time_ms
                    }
                else:
                    return {
                        "status": "failed",
                        "token_address": token_address,
                        "error": "No score calculated"
                    }
            finally:
                db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error calculating score", "details": {"error": str(e)}})


@router.post("/calculate-all")
async def calculate_all_scores():
    """
    Рассчитать скоры для всех активных токенов
    """
    try:
        # Запускаем через Celery task
        task = calculate_scores_for_active_tokens_task.delay()
        
        return {
            "message": "Score calculation for all active tokens initiated",
            "task_id": task.id,
            "status": "calculating"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error calculating all scores", "details": {"error": str(e)}})


@router.post("/reload-model")
async def reload_scoring_model():
    """
    Перезагрузить модель скоринга из конфигурации
    """
    try:
        # Запускаем через Celery task
        task = reload_scoring_model_task.delay()
        
        return {
            "message": "Scoring model reload initiated",
            "task_id": task.id,
            "status": "reloading"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error reloading model", "details": {"error": str(e)}})


@router.post("/test")
async def test_scoring_model(
    test_token: str = Query("So11111111111111111111111111111111111111112", description="Токен для тестирования")
):
    """
    Тестирование модели скоринга
    """
    try:
        # Запускаем через Celery task
        task = test_scoring_model_task.delay(test_token)
        
        return {
            "message": f"Scoring model test initiated with token {test_token}",
            "task_id": task.id,
            "status": "testing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error testing scoring model", "details": {"error": str(e)}})


@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """
    Получить список доступных моделей скоринга
    """
    try:
        models = scoring_manager.get_available_models()
        
        return {
            "available_models": models,
            "total_models": len(models),
            "active_models": len([m for m in models if m.get("available", False)])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting available models", "details": {"error": str(e)}})


@router.get("/scores/{token_id}")
async def get_token_scores_history(
    token_id: UUID,
    model_name: Optional[str] = Query(None, description="Фильтр по модели"),
    hours_back: int = Query(24, ge=1, le=168, description="Часов назад"),
    limit: int = Query(100, ge=1, le=1000, description="Максимум записей"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить историю скоров токена
    """
    try:
        # Проверяем существование токена
        token = token_crud.get(db, id=token_id)
        if not token:
            raise HTTPException(status_code=404, detail={"message": "Token not found", "details": {"token_id": str(token_id)}})
        
        # Получаем скоры
        scores = token_scores_crud.get_by_token(
            db,
            token_id=token_id,
            model_name=model_name,
            hours_back=hours_back,
            limit=limit
        )
        
        # Преобразуем в JSON
        scores_data = []
        for score in scores:
            scores_data.append({
                "id": str(score.id),
                "model_name": score.model_name,
                "score_value": score.score_value,
                "calculated_at": score.calculated_at.isoformat(),
                "components": score.components
            })
        
        return {
            "token_id": str(token_id),
            "token_address": token.token_address,
            "scores": scores_data,
            "total_records": len(scores_data),
            "model_filter": model_name,
            "hours_back": hours_back
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/top-tokens")
async def get_top_scored_tokens(
    model_name: str = Query("hybrid_momentum_v1", description="Модель для ранжирования"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Минимальный скор"),
    limit: int = Query(10, ge=1, le=100, description="Количество токенов"),
    hours_back: int = Query(1, ge=1, le=24, description="Период для поиска"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить топ токены по скору
    """
    try:
        top_tokens = token_scores_crud.get_top_tokens(
            db,
            model_name=model_name,
            min_score=min_score,
            limit=limit,
            hours_back=hours_back
        )
        
        # Дополняем данными токенов
        enriched_tokens = []
        for token_data in top_tokens:
            token = token_crud.get(db, id=UUID(token_data["token_id"]))
            if token:
                enriched_tokens.append({
                    "token_id": token_data["token_id"],
                    "token_address": token.token_address,
                    "score_value": token_data["score_value"],
                    "calculated_at": token_data["calculated_at"],
                    "components": token_data.get("components"),
                    "status": token.status.value,
                    "pools_count": len(token.pools)
                })
        
        return {
            "top_tokens": enriched_tokens,
            "model_name": model_name,
            "min_score": min_score,
            "total_found": len(enriched_tokens),
            "period_hours": hours_back,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/stats")
async def get_scoring_stats() -> Dict[str, Any]:
    """
    Получить статистику scoring engine
    """
    try:
        # Запускаем через Celery task для консистентности
        task = get_scoring_stats_task.delay()
        
        return {
            "message": "Scoring stats retrieval initiated",
            "task_id": task.id,
            "status": "fetching"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting scoring stats", "details": {"error": str(e)}})


@router.get("/config")
async def get_scoring_config(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получить текущую конфигурацию скоринга
    """
    try:
        from app.crud import system_crud
        
        # Получаем параметры скоринга
        scoring_params = {}
        scoring_keys = [
            "SCORING_MODEL",
            "SCORING_WEIGHTS", 
            "EWMA_ALPHA",
            "MIN_SCORE_THRESHOLD"
        ]
        
        for key in scoring_keys:
            config = system_crud.get_by_key(db, key=key)
            if config:
                scoring_params[key] = {
                    "value": config.value,
                    "description": config.description,
                    "updated_at": config.updated_at.isoformat()
                }
        
        return {
            "scoring_config": scoring_params,
            "total_params": len(scoring_params)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.put("/config/{key}")
async def update_scoring_config(
    key: str,
    value: dict,  # {"value": new_value, "description": optional_description}
    db: Session = Depends(get_db)
):
    """
    Обновить параметр конфигурации скоринга
    """
    try:
        # Разрешенные ключи для скоринга
        allowed_keys = [
            "SCORING_MODEL",
            "SCORING_WEIGHTS",
            "EWMA_ALPHA", 
            "MIN_SCORE_THRESHOLD"
        ]
        
        if key not in allowed_keys:
            raise HTTPException(
                status_code=400,
                detail={"message": "Key not allowed", "details": {"key": key, "allowed": allowed_keys}},
            )
        
        if "value" not in value:
            raise HTTPException(status_code=400, detail={"message": "Missing field", "details": {"missing": "value"}})
        
        # Валидация значений
        new_value = value["value"]
        description = value.get("description")
        
        if key == "SCORING_WEIGHTS":
            # Проверяем что веса в сумме дают 1.0
            if isinstance(new_value, dict):
                weights_sum = sum(new_value.values())
                if abs(weights_sum - 1.0) > 0.001:
                    raise HTTPException(status_code=400, detail={"message": "Weights sum must be 1.0", "details": {"sum": weights_sum}})
        
        elif key == "EWMA_ALPHA":
            # Проверяем диапазон EWMA
            if not (0.0 <= float(new_value) <= 1.0):
                raise HTTPException(status_code=400, detail={"message": "EWMA_ALPHA must be between 0.0 and 1.0", "details": {"given": new_value}})
        
        elif key == "SCORING_MODEL":
            # Проверяем что модель существует
            available_models = ["hybrid_momentum_v1"]  # Список доступных моделей
            if new_value not in available_models:
                raise HTTPException(status_code=400, detail={"message": "Unknown model", "details": {"given": new_value, "available": available_models}})
        
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
        
        # Запускаем перезагрузку модели
        reload_task = reload_scoring_model_task.delay()
        
        return {
            "message": f"Scoring config '{key}' updated successfully",
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "updated_at": config.updated_at.isoformat(),
            "reload_task_id": reload_task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/top-tokens")
async def get_top_tokens_by_score(
    model_name: str = Query("hybrid_momentum_v1", description="Модель скоринга"),
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Минимальный скор"),
    limit: int = Query(10, ge=1, le=100, description="Количество токенов"),
    hours_back: int = Query(1, ge=1, le=24, description="Период поиска"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить топ токены по скору (для TOML экспорта)
    """
    try:
        top_tokens = token_scores_crud.get_top_tokens(
            db,
            model_name=model_name,
            min_score=min_score,
            limit=limit,
            hours_back=hours_back
        )
        
        # Обогащаем данными токенов и пулов
        enriched_tokens = []
        for token_data in top_tokens:
            token = token_crud.get(db, id=UUID(token_data["token_id"]))
            if token:
                # Получаем активные пулы
                from app.crud import pool_crud
                active_pools = pool_crud.get_by_token(
                    db, 
                    token_id=token.id,
                    active_only=True
                )
                
                pool_data = []
                for pool in active_pools:
                    pool_data.append({
                        "pool_address": pool.pool_address,
                        "dex_name": pool.dex_name,
                        "is_active": pool.is_active
                    })
                
                enriched_tokens.append({
                    "token_address": token.token_address,
                    "score_value": token_data["score_value"],
                    "calculated_at": token_data["calculated_at"],
                    "status": token.status.value,
                    "pools": pool_data,
                    "pools_count": len(pool_data),
                    "components": token_data.get("components")
                })
        
        return {
            "top_tokens": enriched_tokens,
            "model_name": model_name,
            "min_score": min_score,
            "total_found": len(enriched_tokens),
            "period_hours": hours_back,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/model-info")
async def get_current_model_info() -> Dict[str, Any]:
    """
    Получить подробную информацию о текущей модели
    """
    try:
        model_info = await scoring_manager.get_model_info()
        return model_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting model info", "details": {"error": str(e)}})


@router.post("/benchmark")
async def benchmark_scoring_model(
    test_tokens: List[str] = Query(
        default=["So11111111111111111111111111111111111111112"],
        description="Список токенов для бенчмарка"
    ),
    iterations: int = Query(1, ge=1, le=10, description="Количество итераций")
) -> Dict[str, Any]:
    """
    Бенчмарк производительности модели скоринга
    """
    try:
        benchmark_results = []
        total_time = 0.0
        
        db = next(get_db())
        try:
            for iteration in range(iterations):
                iteration_results = []
                iteration_start = datetime.now()
                
                for token_address in test_tokens:
                    result = await scoring_manager.test_model_calculation(token_address, db)
                    
                    if result.get("status") == "success":
                        iteration_results.append({
                            "token_address": token_address,
                            "score": result.get("score_smoothed"),
                            "execution_time_ms": result.get("execution_time_ms")
                        })
                
                iteration_time = (datetime.now() - iteration_start).total_seconds() * 1000
                total_time += iteration_time
                
                benchmark_results.append({
                    "iteration": iteration + 1,
                    "results": iteration_results,
                    "iteration_time_ms": iteration_time,
                    "tokens_processed": len(iteration_results)
                })
        
        finally:
            db.close()
        
        avg_time = total_time / iterations if iterations > 0 else 0
        avg_per_token = avg_time / len(test_tokens) if test_tokens else 0
        
        return {
            "benchmark_results": benchmark_results,
            "summary": {
                "total_iterations": iterations,
                "total_tokens": len(test_tokens),
                "total_time_ms": total_time,
                "average_time_per_iteration_ms": avg_time,
                "average_time_per_token_ms": avg_per_token
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Benchmark error", "details": {"error": str(e)}})
