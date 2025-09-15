"""
TOML export endpoints for arbitrage bot
"""

from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.toml_export.generator import toml_generator

router = APIRouter(tags=["export"])


@router.get("/config/dynamic_strategy.toml", response_class=PlainTextResponse)
async def get_dynamic_strategy_toml(
    response: Response,
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Переопределить min_score_for_config"),
    top_count: Optional[int] = Query(None, ge=1, le=10, description="Переопределить количество токенов"),
    model: Optional[str] = Query(None, description="Переопределить модель скоринга"),
    db: Session = Depends(get_db)
) -> str:
    """
    Публичный endpoint для получения TOML конфигурации арбитражного бота
    
    URL: /config/dynamic_strategy.toml
    
    Логика согласно ФЗ:
    1. Отбирает токены в статусе Active
    2. Фильтрует по min_score_for_config 
    3. Сортирует по Score убыванию
    4. Выбирает топ-3 токена
    5. Включает их активные пулы
    """
    try:
        # Устанавливаем заголовки для TOML
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = "inline; filename=dynamic_strategy.toml"
        
        # Кеширование на 1 минуту (согласно Nginx конфигурации)
        response.headers["Cache-Control"] = "public, max-age=60"
        response.headers["Last-Modified"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # Генерируем TOML
        if any([min_score is not None, top_count is not None, model is not None]):
            # Кастомные параметры
            toml_content = await toml_generator.generate_custom_toml(
                db,
                min_score=min_score,
                top_count=top_count, 
                model_name=model
            )
        else:
            # Стандартная конфигурация
            toml_content = await toml_generator.generate_dynamic_strategy_toml(db)
        
        return toml_content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to generate TOML config", "details": {"error": str(e)}})


@router.get("/config/preview")
async def get_export_preview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Предварительный просмотр экспорта без генерации TOML
    """
    try:
        preview = await toml_generator.get_export_preview(db)
        return preview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get export preview", "details": {"error": str(e)}})


@router.get("/config/validate")
async def validate_export_config(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Валидация конфигурации экспорта
    """
    try:
        validation = await toml_generator.validate_export_config(db)
        return validation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to validate export config", "details": {"error": str(e)}})


@router.get("/config/stats")
async def get_export_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Статистика TOML экспорта
    """
    try:
        # Статистика генератора
        generator_stats = toml_generator.get_stats()
        
        # Дополнительная статистика из БД
        from app.crud import system_crud, token_crud
        from app.models.token import TokenStatus
        
        # Текущие параметры экспорта
        export_config = await toml_generator._load_export_config(db)
        
        # Статистика активных токенов
        active_tokens_count = token_crud.count_by_status(db, status=TokenStatus.ACTIVE)
        
        # Токены с высоким скором
        from app.crud.metrics import token_scores_crud
        high_score_tokens = token_scores_crud.get_top_tokens(
            db,
            model_name=export_config["scoring_model"],
            min_score=export_config["min_score_for_config"],
            limit=100,  # Все подходящие
            hours_back=2
        )
        
        return {
            "generator_stats": generator_stats,
            "export_config": export_config,
            "active_tokens_count": active_tokens_count,
            "high_score_tokens_count": len(high_score_tokens),
            "export_eligibility_rate": (
                len(high_score_tokens) / active_tokens_count 
                if active_tokens_count > 0 else 0
            ),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to get export stats", "details": {"error": str(e)}})


@router.post("/config/test-generation")
async def test_toml_generation(
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Тестовый min_score"),
    top_count: int = Query(3, ge=1, le=10, description="Тестовое количество токенов"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Тестовая генерация TOML с кастомными параметрами
    """
    try:
        # Генерируем тестовый TOML
        toml_content = await toml_generator.generate_custom_toml(
            db,
            min_score=min_score,
            top_count=top_count
        )
        
        # Анализируем результат
        import toml as toml_parser
        parsed_config = toml_parser.loads(toml_content)
        
        return {
            "status": "success",
            "toml_content": toml_content,
            "parsed_config": parsed_config,
            "size_bytes": len(toml_content.encode('utf-8')),
            "tokens_included": len(parsed_config.get("tokens", [])),
            "generation_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to test TOML generation", "details": {"error": str(e)}})


@router.get("/config/sample")
async def get_sample_toml() -> Dict[str, Any]:
    """
    Получить пример TOML конфигурации для документации
    """
    try:
        sample_config = {
            "strategy": {
                "name": "dynamic_strategy",
                "description": "ToTheMoon2 dynamic arbitrage strategy",
                "version": "1.0.0",
                "generated_at": "2025-09-14T12:00:00Z",
                "model_name": "hybrid_momentum_v1",
                "min_score_threshold": 0.7,
                "tokens_count": 3
            },
            "tokens": [
                {
                    "address": "TokenAddress1111111111111111111111111111",
                    "score": 0.85,
                    "calculated_at": "2025-09-14T12:00:00Z",
                    "status": "active",
                    "pools_count": 2,
                    "pools": {
                        "raydium": ["PoolAddress1111111111111111111111111111"],
                        "orca": ["PoolAddress2222222222222222222222222222"]
                    },
                    "metadata": {
                        "token_id": "uuid-here",
                        "last_score_calculated": "2025-09-14T12:00:00Z",
                        "activated_at": "2025-09-14T10:00:00Z"
                    }
                },
                {
                    "address": "TokenAddress3333333333333333333333333333",
                    "score": 0.78,
                    "calculated_at": "2025-09-14T12:00:00Z",
                    "status": "active",
                    "pools_count": 1,
                    "pools": {
                        "raydium": ["PoolAddress4444444444444444444444444444"]
                    },
                    "metadata": {
                        "token_id": "uuid-here-2",
                        "last_score_calculated": "2025-09-14T12:00:00Z",
                        "activated_at": "2025-09-14T09:00:00Z"
                    }
                }
            ],
            "metadata": {
                "source": "ToTheMoon2",
                "generation_time": "2025-09-14T12:00:00Z",
                "tokens_selected": 2,
                "total_pools": 3,
                "selection_criteria": {
                    "status": "active",
                    "min_score": 0.7,
                    "top_count": 3,
                    "model": "hybrid_momentum_v1"
                }
            }
        }
        
        # Конвертируем в TOML
        import toml
        toml_content = toml.dumps(sample_config)
        
        return {
            "sample_toml": toml_content,
            "parsed_config": sample_config,
            "description": "Пример TOML конфигурации для NotArb бота",
            "usage": "Используйте GET /config/dynamic_strategy.toml для получения реальной конфигурации"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Failed to generate sample TOML", "details": {"error": str(e)}})
