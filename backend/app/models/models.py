
from typing import List, Optional
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class TokenMetricHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    tx_count: int
    volume: float
    holder_count: int
    buys_volume: float
    sells_volume: float

    token_id: Optional[int] = Field(default=None, foreign_key="token.id")
    token: Optional["Token"] = Relationship(back_populates="metric_history")


class Token(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token_address: str = Field(index=True, unique=True)
    name: Optional[str] = Field(default=None, index=True)
    status: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    activated_at: Optional[datetime] = Field(default=None)
    last_score_value: Optional[float] = Field(default=None)
    last_smoothed_score: Optional[float] = Field(default=None)
    low_score_since: Optional[datetime] = Field(default=None)
    low_activity_streak: int = Field(default=0, nullable=False)
    last_updated: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    pools: List["Pool"] = Relationship(back_populates="token")
    metric_history: List[TokenMetricHistory] = Relationship(back_populates="token")


class Pool(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pool_address: str = Field(index=True, unique=True)
    dex_name: str

    token_id: Optional[int] = Field(default=None, foreign_key="token.id")
    token: Optional[Token] = Relationship(back_populates="pools")


class ScoringParameter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    param_name: str = Field(unique=True)
    param_value: float
    is_active: bool = Field(default=True)

