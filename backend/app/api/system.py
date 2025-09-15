"""
System configuration and statistics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import system_crud, token_crud
from app.schemas.system import SystemConfigResponse, SystemStatsResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config(db: Session = Depends(get_db)) -> SystemConfigResponse:
    """
    Получение системной конфигурации
    """
    try:
        config_by_category = system_crud.get_all_grouped(db)
        total_params = db.query(system_crud.model).count()
        
        return SystemConfigResponse(
            config=config_by_category,
            total_params=total_params
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/stats", response_model=SystemStatsResponse)
async def get_stats(db: Session = Depends(get_db)) -> SystemStatsResponse:
    """
    Статистика по токенам в системе
    """
    try:
        stats = token_crud.get_stats(db)
        
        # Добавляем количество конфигурационных параметров
        stats["config_params"] = db.query(system_crud.model).count()
        
        return SystemStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/config/{key}")
async def get_config_value(key: str, db: Session = Depends(get_db)):
    """
    Получить значение конкретного параметра конфигурации
    """
    try:
        config = system_crud.get_by_key(db, key=key)
        if not config:
            raise HTTPException(status_code=404, detail={"message": "Config parameter not found", "details": {"key": key}})
        
        return {
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "category": config.category,
            "updated_at": config.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.put("/config/{key}")
async def update_config_value(
    key: str, 
    value: dict,  # Ожидаем {"value": new_value, "description": optional_description}
    db: Session = Depends(get_db)
):
    """
    Обновить значение параметра конфигурации
    """
    try:
        if "value" not in value:
            raise HTTPException(status_code=400, detail={"message": "Missing field", "details": {"missing": "value"}})
        
        new_value = value["value"]
        description = value.get("description")
        
        config = system_crud.update_by_key(
            db, 
            key=key, 
            value=new_value, 
            description=description
        )
        
        if not config:
            raise HTTPException(status_code=404, detail={"message": "Config parameter not found", "details": {"key": key}})
        
        return {
            "message": f"Config parameter '{key}' updated successfully",
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "updated_at": config.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})
