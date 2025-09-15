"""
Database configuration and session management
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


# Database URL из environment переменных
DATABASE_URL = os.getenv("DATABASE_URL")

# Base класс для всех моделей (всегда доступен)
Base = declarative_base()

# Engine и Session создаются только если есть DATABASE_URL
engine = None
SessionLocal = None

if DATABASE_URL:
    # Создание engine с оптимизацией для 2 ГБ RAM
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,  # Ограничиваем connection pool
        max_overflow=10,
        pool_pre_ping=True,  # Проверка соединений
        echo=os.getenv("LOG_LEVEL") == "DEBUG"  # SQL логирование только в debug
    )

    # Session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения database session в FastAPI
    """
    if not SessionLocal:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Создание всех таблиц (для тестирования)
    В продакшене используется Alembic
    """
    Base.metadata.create_all(bind=engine)
