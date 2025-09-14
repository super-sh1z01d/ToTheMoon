"""
Health check and system info endpoints
"""

import os
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import HealthStatus
from app.schemas.system import AppInfoResponse

router = APIRouter()

# Глобальные переменные для подключений
redis_client = None


def get_redis_client():
    """Получение Redis клиента с обработкой ошибок"""
    global redis_client
    if redis_client is None:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = redis.from_url(redis_url, decode_responses=True)
            # Проверка подключения
            redis_client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            redis_client = None
    return redis_client


@router.get("/health", response_model=HealthStatus)
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint для мониторинга состояния сервисов
    """
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "services": {
            "api": "healthy",
            "redis": "unknown",
            "postgres": "unknown"
        }
    }
    
    # Проверка Redis
    try:
        redis_conn = get_redis_client()
        if redis_conn and redis_conn.ping():
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "unhealthy"
    except Exception:
        health_status["services"]["redis"] = "unhealthy"
    
    # Проверка PostgreSQL через SQLAlchemy
    try:
        # Простой запрос для проверки соединения
        db.execute("SELECT 1")
        health_status["services"]["postgres"] = "healthy"
    except Exception:
        health_status["services"]["postgres"] = "unhealthy"
    
    # Определение общего статуса
    if any(status == "unhealthy" for status in health_status["services"].values()):
        health_status["status"] = "degraded"
        return JSONResponse(
            status_code=503,
            content=health_status
        )
    
    return health_status


@router.get("/info", response_model=AppInfoResponse)
async def get_info() -> AppInfoResponse:
    """
    Информация о приложении
    """
    return AppInfoResponse(
        name="ToTheMoon2",
        version="1.0.0",
        description="Система скоринга токенов Solana",
        environment=os.getenv("ENVIRONMENT", "development"),
        features=[
            "Token discovery via WebSocket",
            "Birdeye API integration", 
            "Scoring engine",
            "TOML export for arbitrage bots"
        ]
    )
