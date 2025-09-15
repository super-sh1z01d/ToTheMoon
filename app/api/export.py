from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.token import TokenStatus
from app.repositories.token import list_tokens

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/bot-config")
async def export_bot_config(session: AsyncSession = Depends(get_session)):
    tokens = await list_tokens(session, status=TokenStatus.ACTIVE, limit=100)
    tokens_sorted = sorted(tokens, key=lambda t: (t.last_score_value or 0.0), reverse=True)
    out = [
        {
            "address": t.address,
            "symbol": t.symbol,
            "score": t.last_score_value or 0.0,
        }
        for t in tokens_sorted
    ]
    return {"tokens": out}

