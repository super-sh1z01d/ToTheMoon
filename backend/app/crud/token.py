"""
CRUD operations for Token model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.token import Token, TokenStatus, TokenStatusHistory, StatusChangeReason
from app.models.pool import Pool
from app.schemas.token import TokenCreate, TokenUpdate


class CRUDToken(CRUDBase[Token, TokenCreate, TokenUpdate]):
    """
    CRUD операции для токенов
    """

    def get_by_address(self, db: Session, *, token_address: str) -> Optional[Token]:
        """
        Получить токен по адресу
        """
        return db.query(Token).filter(Token.token_address == token_address).first()

    def get_by_status(
        self, 
        db: Session, 
        *, 
        status: TokenStatus, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Token]:
        """
        Получить токены по статусу
        """
        return (
            db.query(Token)
            .filter(Token.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_status(self, db: Session, *, status: TokenStatus) -> int:
        """
        Подсчет токенов по статусу
        """
        return db.query(Token).filter(Token.status == status).count()

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """
        Получить статистику по токенам
        """
        stats = {
            "total_tokens": db.query(Token).count(),
            "by_status": {}
        }
        
        # Подсчет по статусам
        for status in TokenStatus:
            count = db.query(Token).filter(Token.status == status).count()
            stats["by_status"][status.value] = count
        
        # Статистика пулов
        stats["total_pools"] = db.query(Pool).count()
        stats["active_pools"] = db.query(Pool).filter(Pool.is_active == True).count()
        
        return stats

    def create_with_history(
        self, 
        db: Session, 
        *, 
        obj_in: TokenCreate,
        reason: StatusChangeReason = StatusChangeReason.DISCOVERY
    ) -> Token:
        """
        Создать токен с записью в историю статусов
        """
        # Проверяем, не существует ли уже такой токен
        existing_token = self.get_by_address(db, token_address=obj_in.token_address)
        if existing_token:
            raise ValueError(f"Token with address {obj_in.token_address} already exists")
        
        # Создаем токен
        token = self.create(db, obj_in=obj_in)
        
        # Создаем запись в истории
        history_entry = TokenStatusHistory(
            token_id=token.id,
            old_status=None,  # NULL для первого создания
            new_status=token.status,
            reason=reason,
            change_metadata=f"Token created with address {token.token_address}"
        )
        
        db.add(history_entry)
        db.commit()
        
        return token

    def update_status(
        self,
        db: Session,
        *,
        token: Token,
        new_status: TokenStatus,
        reason: StatusChangeReason,
        metadata: Optional[str] = None
    ) -> Token:
        """
        Обновить статус токена с записью в историю
        """
        old_status = token.status
        
        if old_status == new_status:
            return token  # Нет изменений
        
        # Обновляем токен
        update_data = {"status": new_status}
        
        # Устанавливаем временные метки
        from datetime import datetime
        now = datetime.now()
        
        if new_status == TokenStatus.ACTIVE:
            update_data["activated_at"] = now
        elif new_status == TokenStatus.ARCHIVED:
            update_data["archived_at"] = now
        
        updated_token = self.update(db, db_obj=token, obj_in=update_data)
        
        # Создаем запись в истории
        history_entry = TokenStatusHistory(
            token_id=token.id,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            change_metadata=metadata or f"Status changed from {old_status.value} to {new_status.value}"
        )
        
        db.add(history_entry)
        db.commit()
        
        return updated_token

    def get_with_pools_count(
        self, 
        db: Session, 
        *,
        skip: int = 0, 
        limit: int = 100,
        status: Optional[TokenStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить токены с количеством пулов
        """
        query = db.query(Token)
        
        if status:
            query = query.filter(Token.status == status)
        
        tokens = query.offset(skip).limit(limit).all()
        
        result = []
        for token in tokens:
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
                "pools_count": db.query(Pool).filter(Pool.token_id == token.id).count()
            }
            result.append(token_dict)
        
        return result


# Создаем экземпляр CRUD для использования
token_crud = CRUDToken(Token)
