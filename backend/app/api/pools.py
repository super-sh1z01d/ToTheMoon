"""
Pool management endpoints
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import pool_crud, token_crud
from app.schemas.pool import PoolCreate, PoolResponse, PoolUpdate

router = APIRouter(prefix="/pools", tags=["pools"])


@router.get("", response_model=List[PoolResponse])
async def get_pools(
    token_id: Optional[UUID] = Query(None, description="Фильтр по ID токена"),
    dex_name: Optional[str] = Query(None, description="Фильтр по названию DEX"),
    active_only: bool = Query(False, description="Показать только активные пулы"),
    limit: int = Query(100, ge=1, le=1000, description="Количество пулов на странице"),
    offset: int = Query(0, ge=0, description="Смещение от начала"),
    db: Session = Depends(get_db)
) -> List[PoolResponse]:
    """
    Получение списка пулов с фильтрацией
    """
    try:
        if token_id:
            # Фильтр по токену
            pools = pool_crud.get_by_token(db, token_id=token_id, active_only=active_only)
        elif dex_name:
            # Фильтр по DEX
            pools = pool_crud.get_by_dex(db, dex_name=dex_name, active_only=active_only)
        else:
            # Общий список с фильтрами
            filters = {}
            if active_only:
                filters["is_active"] = True
            
            pools = pool_crud.get_multi(db, skip=offset, limit=limit, filters=filters)
        
        # Преобразуем в схемы ответа
        pools_response = []
        for pool in pools:
            pools_response.append(PoolResponse(
                id=str(pool.id),
                pool_address=pool.pool_address,
                token_id=str(pool.token_id),
                dex_name=pool.dex_name,
                is_active=pool.is_active,
                created_at=pool.created_at,
                updated_at=pool.updated_at
            ))
        
        return pools_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.post("", response_model=PoolResponse, status_code=201)
async def create_pool(
    pool: PoolCreate,
    db: Session = Depends(get_db)
) -> PoolResponse:
    """
    Создание нового пула ликвидности
    """
    try:
        # Проверяем существование токена
        token = token_crud.get(db, id=UUID(pool.token_id))
        if not token:
            raise HTTPException(status_code=404, detail={"message": "Token not found", "details": {"token_id": pool.token_id}})
        
        # Проверяем, не существует ли уже пул с таким адресом
        existing_pool = pool_crud.get_by_address(db, pool_address=pool.pool_address)
        if existing_pool:
            raise HTTPException(
                status_code=400,
                detail={"message": "Pool already exists", "details": {"pool_address": pool.pool_address}},
            )
        
        # Создаем пул
        created_pool = pool_crud.create(db, obj_in=pool)
        
        return PoolResponse(
            id=str(created_pool.id),
            pool_address=created_pool.pool_address,
            token_id=str(created_pool.token_id),
            dex_name=created_pool.dex_name,
            is_active=created_pool.is_active,
            created_at=created_pool.created_at,
            updated_at=created_pool.updated_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": "Bad request", "details": {"error": str(e)}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/{pool_id}", response_model=PoolResponse)
async def get_pool(
    pool_id: UUID,
    db: Session = Depends(get_db)
) -> PoolResponse:
    """
    Получение информации о конкретном пуле
    """
    try:
        pool = pool_crud.get(db, id=pool_id)
        if not pool:
            raise HTTPException(status_code=404, detail={"message": "Pool not found", "details": {"pool_id": str(pool_id)}})
        
        return PoolResponse(
            id=str(pool.id),
            pool_address=pool.pool_address,
            token_id=str(pool.token_id),
            dex_name=pool.dex_name,
            is_active=pool.is_active,
            created_at=pool.created_at,
            updated_at=pool.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.put("/{pool_id}", response_model=PoolResponse)
async def update_pool(
    pool_id: UUID,
    pool_update: PoolUpdate,
    db: Session = Depends(get_db)
) -> PoolResponse:
    """
    Обновление информации о пуле
    """
    try:
        pool = pool_crud.get(db, id=pool_id)
        if not pool:
            raise HTTPException(status_code=404, detail={"message": "Pool not found", "details": {"pool_id": str(pool_id)}})
        
        # Обновляем пул
        updated_pool = pool_crud.update(db, db_obj=pool, obj_in=pool_update)
        
        return PoolResponse(
            id=str(updated_pool.id),
            pool_address=updated_pool.pool_address,
            token_id=str(updated_pool.token_id),
            dex_name=updated_pool.dex_name,
            is_active=updated_pool.is_active,
            created_at=updated_pool.created_at,
            updated_at=updated_pool.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.delete("/{pool_id}")
async def delete_pool(
    pool_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Удаление пула
    """
    try:
        pool = pool_crud.get(db, id=pool_id)
        if not pool:
            raise HTTPException(status_code=404, detail={"message": "Pool not found", "details": {"pool_id": str(pool_id)}})
        
        pool_crud.remove(db, id=pool_id)
        
        return {"message": f"Pool {pool.pool_address} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.post("/{pool_id}/activate", response_model=PoolResponse)
async def activate_pool(
    pool_id: UUID,
    db: Session = Depends(get_db)
) -> PoolResponse:
    """
    Активировать пул
    """
    try:
        updated_pool = pool_crud.activate_pool(db, pool_id=pool_id)
        if not updated_pool:
            raise HTTPException(status_code=404, detail={"message": "Pool not found", "details": {"pool_id": str(pool_id)}})
        
        return PoolResponse(
            id=str(updated_pool.id),
            pool_address=updated_pool.pool_address,
            token_id=str(updated_pool.token_id),
            dex_name=updated_pool.dex_name,
            is_active=updated_pool.is_active,
            created_at=updated_pool.created_at,
            updated_at=updated_pool.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.post("/{pool_id}/deactivate", response_model=PoolResponse)
async def deactivate_pool(
    pool_id: UUID,
    db: Session = Depends(get_db)
) -> PoolResponse:
    """
    Деактивировать пул
    """
    try:
        updated_pool = pool_crud.deactivate_pool(db, pool_id=pool_id)
        if not updated_pool:
            raise HTTPException(status_code=404, detail={"message": "Pool not found", "details": {"pool_id": str(pool_id)}})
        
        return PoolResponse(
            id=str(updated_pool.id),
            pool_address=updated_pool.pool_address,
            token_id=str(updated_pool.token_id),
            dex_name=updated_pool.dex_name,
            is_active=updated_pool.is_active,
            created_at=updated_pool.created_at,
            updated_at=updated_pool.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})
