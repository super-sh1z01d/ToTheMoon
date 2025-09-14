"""
CRUD operations for System models
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.system import SystemConfig
from app.schemas.system import SystemConfigUpdate


class CRUDSystemConfig(CRUDBase[SystemConfig, dict, SystemConfigUpdate]):
    """
    CRUD операции для системной конфигурации
    """

    def get_by_key(self, db: Session, *, key: str) -> Optional[SystemConfig]:
        """
        Получить параметр конфигурации по ключу
        """
        return db.query(SystemConfig).filter(SystemConfig.key == key).first()

    def get_by_category(self, db: Session, *, category: str) -> list[SystemConfig]:
        """
        Получить параметры конфигурации по категории
        """
        return db.query(SystemConfig).filter(SystemConfig.category == category).all()

    def get_all_grouped(self, db: Session) -> Dict[str, Dict[str, Any]]:
        """
        Получить всю конфигурацию, сгруппированную по категориям
        """
        configs = db.query(SystemConfig).all()
        
        result = {}
        for config in configs:
            category = config.category or "general"
            if category not in result:
                result[category] = {}
            
            result[category][config.key] = {
                "value": config.value,
                "description": config.description,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            }
        
        return result

    def update_by_key(
        self, 
        db: Session, 
        *, 
        key: str, 
        value: Any, 
        description: Optional[str] = None
    ) -> Optional[SystemConfig]:
        """
        Обновить параметр конфигурации по ключу
        """
        config = self.get_by_key(db, key=key)
        if config:
            update_data = {"value": value}
            if description is not None:
                update_data["description"] = description
            
            return self.update(db, db_obj=config, obj_in=update_data)
        return None

    def get_value(self, db: Session, *, key: str, default: Any = None) -> Any:
        """
        Получить значение параметра конфигурации
        """
        config = self.get_by_key(db, key=key)
        return config.value if config else default

    def set_value(
        self, 
        db: Session, 
        *, 
        key: str, 
        value: Any, 
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> SystemConfig:
        """
        Установить значение параметра конфигурации (создать или обновить)
        """
        config = self.get_by_key(db, key=key)
        
        if config:
            # Обновляем существующий
            update_data = {"value": value}
            if description is not None:
                update_data["description"] = description
            if category is not None:
                update_data["category"] = category
            
            return self.update(db, db_obj=config, obj_in=update_data)
        else:
            # Создаем новый
            create_data = {
                "key": key,
                "value": value,
                "description": description,
                "category": category
            }
            return self.create(db, obj_in=create_data)


# Создаем экземпляр CRUD для использования
system_crud = CRUDSystemConfig(SystemConfig)
