from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenCreate(BaseModel):
    address: str = Field(min_length=1)
    symbol: Optional[str] = None


class TokenOut(BaseModel):
    id: int
    address: str
    symbol: Optional[str] = None
    status: str
    created_at: datetime
    activated_at: Optional[datetime] = None
    last_score_value: Optional[float] = None

    model_config = {
        "from_attributes": True,
    }

