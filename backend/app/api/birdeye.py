"""
Birdeye API integration endpoints
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.data_sources.birdeye_client import birdeye_manager
from app.crud import token_crud, token_metrics_crud, birdeye_raw_data_crud
from app.workers.birdeye_tasks import (
    fetch_token_metrics_task,
    fetch_metrics_for_active_tokens_task,
    test_birdeye_connection_task,
    get_birdeye_stats_task
)

router = APIRouter(prefix="/birdeye", tags=["birdeye"])


@router.get("/status")
async def get_birdeye_status() -> Dict[str, Any]:
    """
    Получить статус Birdeye API интеграции
    """
    try:
        stats = birdeye_manager.get_stats()
        return {
            "status": "configured" if stats.get("client_initialized") else "not_configured",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting Birdeye status", "details": {"error": str(e)}})


@router.post("/test")
async def test_birdeye_connection():
    """
    Тестовое подключение к Birdeye API
    """
    try:
        # Запускаем тест через Celery task
        task = test_birdeye_connection_task.delay()
        
        return {
            "message": "Birdeye connection test initiated",
            "task_id": task.id,
            "status": "testing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error testing Birdeye connection", "details": {"error": str(e)}})


@router.post("/fetch/{token_address}")
async def fetch_token_metrics(
    token_address: str,
    save_to_db: bool = Query(True, description="Сохранить метрики в БД")
) -> Dict[str, Any]:
    """
    Получить метрики конкретного токена
    """
    try:
        if save_to_db:
            # Запускаем через Celery task
            task = fetch_token_metrics_task.delay(token_address)
            
            return {
                "message": f"Metrics fetch initiated for {token_address}",
                "task_id": task.id,
                "status": "fetching"
            }
        else:
            # Прямое получение данных (для тестирования)
            if not birdeye_manager.client:
                await birdeye_manager.initialize()
            
            metrics = await birdeye_manager.fetch_token_metrics(token_address)
            
            if metrics:
                return {
                    "status": "success",
                    "token_address": token_address,
                    "metrics": metrics
                }
            else:
                return {
                    "status": "failed",
                    "token_address": token_address,
                    "error": "No metrics data received"
                }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error fetching token metrics", "details": {"error": str(e)}})


@router.post("/fetch-all")
async def fetch_all_active_tokens():
    """
    Получить метрики всех активных токенов
    """
    try:
        # Запускаем через Celery task
        task = fetch_metrics_for_active_tokens_task.delay()
        
        return {
            "message": "Metrics fetch for all active tokens initiated",
            "task_id": task.id,
            "status": "fetching"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error fetching all metrics", "details": {"error": str(e)}})


@router.get("/metrics/{token_id}")
async def get_token_metrics_history(
    token_id: UUID,
    hours_back: int = Query(24, ge=1, le=168, description="Часов назад для получения истории"),
    limit: int = Query(100, ge=1, le=1000, description="Максимум записей"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить историю метрик токена из БД
    """
    try:
        # Проверяем существование токена
        token = token_crud.get(db, id=token_id)
        if not token:
            raise HTTPException(status_code=404, detail={"message": "Token not found", "details": {"token_id": str(token_id)}})
        
        # Получаем метрики
        metrics = token_metrics_crud.get_by_token(
            db, 
            token_id=token_id,
            hours_back=hours_back,
            limit=limit
        )
        
        # Получаем сводку
        summary = token_metrics_crud.get_metrics_summary(
            db,
            token_id=token_id,
            hours_back=hours_back
        )
        
        # Преобразуем в JSON-совместимый формат
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                "id": str(metric.id),
                "timestamp": metric.timestamp.isoformat(),
                "tx_count_5m": metric.tx_count_5m,
                "tx_count_1h": metric.tx_count_1h,
                "volume_5m_usd": float(metric.volume_5m_usd),
                "volume_1h_usd": float(metric.volume_1h_usd),
                "buys_volume_5m_usd": float(metric.buys_volume_5m_usd),
                "sells_volume_5m_usd": float(metric.sells_volume_5m_usd),
                "holders_count": metric.holders_count,
                "liquidity_usd": float(metric.liquidity_usd)
            })
        
        return {
            "token_id": str(token_id),
            "token_address": token.token_address,
            "metrics": metrics_data,
            "summary": summary,
            "total_records": len(metrics_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/raw-data/{token_address}")
async def get_raw_data(
    token_address: str,
    endpoint: Optional[str] = Query(None, description="Фильтр по endpoint"),
    include_expired: bool = Query(False, description="Включить устаревшие данные"),
    limit: int = Query(10, ge=1, le=100, description="Максимум записей"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить raw данные токена от Birdeye API
    """
    try:
        if endpoint:
            # Конкретный endpoint
            raw_data_list = birdeye_raw_data_crud.get_by_token_and_endpoint(
                db,
                token_address=token_address,
                endpoint=endpoint,
                include_expired=include_expired
            )
        else:
            # Все endpoints
            from app.models.raw_data import BirdeyeRawData
            from sqlalchemy import and_
            
            query = db.query(BirdeyeRawData).filter(
                BirdeyeRawData.token_address == token_address
            )
            
            if not include_expired:
                query = query.filter(BirdeyeRawData.expires_at > datetime.now())
            
            raw_data_list = query.order_by(
                BirdeyeRawData.fetched_at.desc()
            ).limit(limit).all()
        
        # Преобразуем в JSON
        raw_data_json = []
        for raw_data in raw_data_list:
            raw_data_json.append({
                "id": str(raw_data.id),
                "endpoint": raw_data.endpoint,
                "fetched_at": raw_data.fetched_at.isoformat(),
                "expires_at": raw_data.expires_at.isoformat(),
                "is_expired": raw_data.is_expired(),
                "response_data": raw_data.response_data
            })
        
        return {
            "token_address": token_address,
            "raw_data": raw_data_json,
            "total_records": len(raw_data_json)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/stats")
async def get_birdeye_api_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Получить статистику Birdeye API интеграции
    """
    try:
        # API статистика
        api_stats = birdeye_manager.get_stats()
        
        # Статистика raw данных
        storage_stats = birdeye_raw_data_crud.get_storage_stats(db)
        
        # Статистика метрик
        from app.models.metrics import TokenMetrics
        metrics_count = db.query(TokenMetrics).count()
        
        # Последние активности
        latest_raw = db.query(birdeye_raw_data_crud.model).order_by(
            birdeye_raw_data_crud.model.fetched_at.desc()
        ).first()
        
        latest_metrics = db.query(TokenMetrics).order_by(
            TokenMetrics.timestamp.desc()
        ).first()
        
        return {
            "api": api_stats,
            "storage": storage_stats,
            "metrics_count": metrics_count,
            "last_raw_data_fetch": latest_raw.fetched_at.isoformat() if latest_raw else None,
            "last_metrics_update": latest_metrics.timestamp.isoformat() if latest_metrics else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error getting Birdeye stats", "details": {"error": str(e)}})


@router.delete("/cleanup")
async def cleanup_birdeye_data():
    """
    Принудительная очистка устаревших данных Birdeye
    """
    try:
        # Запускаем через Celery task
        from app.workers.birdeye_tasks import cleanup_old_birdeye_data_task
        task = cleanup_old_birdeye_data_task.delay()
        
        return {
            "message": "Birdeye data cleanup initiated",
            "task_id": task.id,
            "status": "cleaning"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Error initiating cleanup", "details": {"error": str(e)}})
