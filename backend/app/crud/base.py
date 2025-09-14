"""
Base CRUD operations
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.base import BaseModel as DBBaseModel

ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Базовый класс для CRUD операций
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete
        """
        self.model = model

    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        """
        Получить объект по ID
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        *,
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Получить список объектов с пагинацией и фильтрами
        """
        query = db.query(self.model)
        
        # Применяем фильтры
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Подсчет количества объектов с фильтрами
        """
        query = db.query(self.model)
        
        # Применяем фильтры
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Создать новый объект
        """
        # Pydantic v2 uses model_dump(); keep backward compatibility if dict() exists
        if hasattr(obj_in, 'model_dump'):
            obj_in_data = obj_in.model_dump()
        elif hasattr(obj_in, 'dict'):
            obj_in_data = obj_in.dict()  # fallback
        else:
            obj_in_data = obj_in
        db_obj = self.model(**obj_in_data)
        
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Integrity error: {str(e)}")
        
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Обновить существующий объект
        """
        obj_data = db_obj.__dict__.copy()
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            if hasattr(obj_in, 'model_dump'):
                update_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)  # fallback
            else:
                update_data = obj_in
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Integrity error: {str(e)}")
        
        return db_obj

    def remove(self, db: Session, *, id: UUID) -> Optional[ModelType]:
        """
        Удалить объект по ID
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
