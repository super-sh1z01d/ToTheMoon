"""
CRUD operations for Pool model
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.pool import Pool
from app.schemas.pool import PoolCreate, PoolUpdate


class CRUDPool(CRUDBase[Pool, PoolCreate, PoolUpdate]):
    """
    CRUD операции для пулов ликвидности
    """

    def get_by_address(self, db: Session, *, pool_address: str) -> Optional[Pool]:
        """
        Получить пул по адресу
        """
        return db.query(Pool).filter(Pool.pool_address == pool_address).first()

    def get_by_token(
        self, 
        db: Session, 
        *, 
        token_id: UUID, 
        active_only: bool = False
    ) -> List[Pool]:
        """
        Получить пулы токена
        """
        query = db.query(Pool).filter(Pool.token_id == token_id)
        
        if active_only:
            query = query.filter(Pool.is_active == True)
            
        return query.all()

    def get_by_dex(
        self, 
        db: Session, 
        *, 
        dex_name: str, 
        active_only: bool = False
    ) -> List[Pool]:
        """
        Получить пулы по DEX
        """
        query = db.query(Pool).filter(Pool.dex_name == dex_name.lower())
        
        if active_only:
            query = query.filter(Pool.is_active == True)
            
        return query.all()

    def count_active(self, db: Session) -> int:
        """
        Подсчет активных пулов
        """
        return db.query(Pool).filter(Pool.is_active == True).count()

    def deactivate_pool(self, db: Session, *, pool_id: UUID) -> Optional[Pool]:
        """
        Деактивировать пул
        """
        pool = self.get(db, id=pool_id)
        if pool:
            return self.update(db, db_obj=pool, obj_in={"is_active": False})
        return None

    def activate_pool(self, db: Session, *, pool_id: UUID) -> Optional[Pool]:
        """
        Активировать пул
        """
        pool = self.get(db, id=pool_id)
        if pool:
            return self.update(db, db_obj=pool, obj_in={"is_active": True})
        return None


# Создаем экземпляр CRUD для использования
pool_crud = CRUDPool(Pool)
