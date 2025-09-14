"""
Alembic environment configuration for ToTheMoon2
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Добавляем app в путь для импорта моделей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base
from app.database import DATABASE_URL

# Alembic Config object
config = context.config

# Интерпретация конфигурационного файла для логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Добавляем MetaData наших моделей для автогенерации миграций
target_metadata = Base.metadata

# Другие значения из конфигурации, определенные в .ini файле
# можно получить здесь:
# my_important_option = config.get_main_option("my_important_option")
# ... и т.д.


def get_database_url() -> str:
    """
    Получаем Database URL из environment переменных
    """
    if DATABASE_URL:
        return DATABASE_URL
    
    # Fallback на переменные окружения
    user = os.getenv("DATABASE_USER", "tothemoon_user")
    password = os.getenv("DATABASE_PASSWORD", "tothemoon_pass")
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME", "tothemoon")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def run_migrations_offline() -> None:
    """
    Запуск миграций в 'offline' режиме.
    
    Этот режим конфигурирует контекст только с URL, 
    без создания Engine. Вызывает Engine.execute()
    для запуска SQL.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Сравнивать типы колонок
        compare_server_default=True,  # Сравнивать default значения
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запуск миграций в 'online' режиме.
    
    В этом сценарии нам нужно создать Engine
    и связать соединение с контекстом.
    """
    # Переопределяем URL из environment
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # Сравнивать типы колонок
            compare_server_default=True,  # Сравнивать default значения
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
