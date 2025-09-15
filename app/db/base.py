from sqlalchemy.orm import DeclarativeBase

# Import models so Alembic can discover metadata on import
from app.models import (  # noqa: F401
    Pool,
    PoolSnapshot,
    Setting,
    Token,
    TokenScore,
    TokenSnapshot,
)


class Base(DeclarativeBase):
    pass
