"""
Token management endpoints
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import token_crud
from app.models.token import TokenStatus
from app.schemas.token import (
    TokenCreate, TokenResponse, TokenUpdate, TokenListResponse,
    TokenStatusHistoryResponse
)

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("", response_model=TokenListResponse)
async def get_tokens(
    status: Optional[str] = Query(None, description="Фильтр по статусу (initial, active, archived)"),
    limit: int = Query(50, ge=1, le=1000, description="Количество токенов на странице"),
    offset: int = Query(0, ge=0, description="Смещение от начала"),
    db: Session = Depends(get_db)
) -> TokenListResponse:
    """
    Получение списка токенов с фильтрацией по статусу и пагинацией
    """
    try:
        # Подготавливаем фильтры
        filters = {}
        if status:
            try:
                status_enum = TokenStatus(status.lower())
                filters["status"] = status_enum
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Invalid status",
                        "details": {
                            "given": status,
                            "allowed": ["initial", "active", "archived"],
                        },
                    },
                )
        
        # Получаем токены с количеством пулов
        if filters:
            tokens_data = token_crud.get_with_pools_count(
                db, 
                skip=offset, 
                limit=limit, 
                status=filters.get("status")
            )
            total = token_crud.count(db, filters=filters)
        else:
            tokens_data = token_crud.get_with_pools_count(
                db, 
                skip=offset, 
                limit=limit
            )
            total = token_crud.count(db)
        
        # Преобразуем в схемы ответа
        tokens_response = []
        for token_data in tokens_data:
            tokens_response.append(TokenResponse(**token_data))
        
        return TokenListResponse(
            tokens=tokens_response,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.post("", response_model=TokenResponse, status_code=201)
async def create_token(
    token: TokenCreate,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Создание нового токена
    """
    try:
        # Проверяем, не существует ли уже токен с таким адресом
        existing_token = token_crud.get_by_address(db, token_address=token.token_address)
        if existing_token:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Token already exists",
                    "details": {"token_address": token.token_address},
                },
            )
        
        # Создаем токен с записью в историю
        created_token = token_crud.create_with_history(db, obj_in=token)
        
        # Получаем количество пулов (будет 0 для нового токена)
        pools_count = 0
        
        # Формируем ответ
        token_dict = {
            "id": str(created_token.id),
            "token_address": created_token.token_address,
            "status": created_token.status.value,
            "created_at": created_token.created_at,
            "updated_at": created_token.updated_at,
            "activated_at": created_token.activated_at,
            "archived_at": created_token.archived_at,
            "last_score_value": created_token.last_score_value,
            "last_score_calculated_at": created_token.last_score_calculated_at,
            "pools_count": pools_count
        }
        
        return TokenResponse(**token_dict)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": "Bad request", "details": {"error": str(e)}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/{token_id}", response_model=TokenResponse)
async def get_token(
    token_id: UUID,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Получение информации о конкретном токене
    """
    try:
        token = token_crud.get(db, id=token_id)
        if not token:
            raise HTTPException(status_code=404, detail={"message": "Token not found", "details": {"token_id": str(token_id)}})
        
        # Получаем количество пулов
        from app.crud import pool_crud
        pools_count = len(pool_crud.get_by_token(db, token_id=token.id))
        
        token_dict = {
            "id": str(token.id),
            "token_address": token.token_address,
            "status": token.status.value,
            "created_at": token.created_at,
            "updated_at": token.updated_at,
            "activated_at": token.activated_at,
            "archived_at": token.archived_at,
            "last_score_value": token.last_score_value,
            "last_score_calculated_at": token.last_score_calculated_at,
            "pools_count": pools_count
        }
        
        return TokenResponse(**token_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.put("/{token_id}", response_model=TokenResponse)
async def update_token(
    token_id: UUID,
    token_update: TokenUpdate,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Обновление информации о токене
    """
    try:
        token = token_crud.get(db, id=token_id)
        if not token:
            raise HTTPException(status_code=404, detail={"message": "Token not found", "details": {"token_id": str(token_id)}})
        
        # Обновляем токен
        updated_token = token_crud.update(db, db_obj=token, obj_in=token_update)
        
        # Получаем количество пулов
        from app.crud import pool_crud
        pools_count = len(pool_crud.get_by_token(db, token_id=updated_token.id))
        
        token_dict = {
            "id": str(updated_token.id),
            "token_address": updated_token.token_address,
            "status": updated_token.status.value,
            "created_at": updated_token.created_at,
            "updated_at": updated_token.updated_at,
            "activated_at": updated_token.activated_at,
            "archived_at": updated_token.archived_at,
            "last_score_value": updated_token.last_score_value,
            "last_score_calculated_at": updated_token.last_score_calculated_at,
            "pools_count": pools_count
        }
        
        return TokenResponse(**token_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.delete("/{token_id}")
async def delete_token(
    token_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Удаление токена
    """
    try:
        token = token_crud.get(db, id=token_id)
        if not token:
            raise HTTPException(status_code=404, detail={"message": "Token not found", "details": {"token_id": str(token_id)}})
        
        token_crud.remove(db, id=token_id)
        
        return {"message": f"Token {token.token_address} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})


@router.get("/{token_id}/history", response_model=List[TokenStatusHistoryResponse])
async def get_token_history(
    token_id: UUID,
    db: Session = Depends(get_db)
) -> List[TokenStatusHistoryResponse]:
    """
    Получение истории изменений статуса токена
    """
    try:
        # Проверяем существование токена
        token = token_crud.get(db, id=token_id)
        if not token:
            raise HTTPException(status_code=404, detail={"message": "Token not found", "details": {"token_id": str(token_id)}})
        
        # Получаем историю
        from app.models.token import TokenStatusHistory
        history = db.query(TokenStatusHistory).filter(
            TokenStatusHistory.token_id == token_id
        ).order_by(TokenStatusHistory.changed_at.desc()).all()
        
        # Преобразуем в схемы ответа
        history_response = []
        for entry in history:
            history_response.append(TokenStatusHistoryResponse(
                id=str(entry.id),
                old_status=entry.old_status,
                new_status=entry.new_status,
                reason=entry.reason.value,
                changed_at=entry.changed_at,
                change_metadata=entry.change_metadata
            ))
        
        return history_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Database error", "details": {"error": str(e)}})
