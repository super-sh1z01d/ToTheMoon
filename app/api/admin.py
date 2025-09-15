from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.settings import get_setting, upsert_setting
from app.schemas.settings import ScoringSettings


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings", response_model=ScoringSettings)
async def get_settings(session: AsyncSession = Depends(get_session)):
    cfg = await get_setting(session, "scoring")
    if not cfg:
        return ScoringSettings().model_dump()
    # Validate and return
    return ScoringSettings(**cfg)


@router.put("/settings", response_model=ScoringSettings)
async def update_settings(payload: ScoringSettings, session: AsyncSession = Depends(get_session)):
    await upsert_setting(session, "scoring", payload.model_dump())
    return payload

