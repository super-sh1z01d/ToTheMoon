"""
ToTheMoon2 FastAPI Application
Система скоринга токенов Solana
"""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

# Импортируем роутеры
from app.api import (
    tokens_router,
    pools_router,
    system_router,
    health_router,
    websocket_router,
    birdeye_router,
    scoring_router,
    lifecycle_router,
    toml_export_router,
    celery_router,
    realtime_router,
)

# Создание FastAPI приложения
app = FastAPI(
    title="ToTheMoon2 API",
    description="Система скоринга токенов Solana для арбитражных возможностей",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS настройки
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
# Health и Info доступны как без префикса, так и под /api для фронтенда
app.include_router(health_router)
app.include_router(health_router, prefix="/api")
app.include_router(tokens_router, prefix="/api")
app.include_router(pools_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(websocket_router, prefix="/api")
app.include_router(birdeye_router, prefix="/api")
app.include_router(scoring_router, prefix="/api")
app.include_router(lifecycle_router, prefix="/api")
app.include_router(celery_router, prefix="/api")
app.include_router(realtime_router, prefix="/api")

# TOML export (БЕЗ префикса /api для публичного доступа)
app.include_router(toml_export_router)

# Удален дублирующий /api/info — теперь он приходит из health_router


# Глобальный обработчик ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Унифицированный обработчик FastAPI HTTPException
    """
    from fastapi.responses import JSONResponse

    detail = exc.detail
    # Приводим к единому формату
    if isinstance(detail, dict):
        details = detail
        message = detail.get("message") or detail.get("detail") or "HTTP error"
    else:
        details = {"detail": detail}
        message = str(detail) if detail else "HTTP error"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": message,
            "details": details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Унифицированный обработчик ошибок валидации (422)
    """
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Validation error",
            "details": {"errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Глобальный обработчик ошибок
    """
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": str(exc) if os.getenv("ENVIRONMENT") == "development" else "Something went wrong",
            "details": None,
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
