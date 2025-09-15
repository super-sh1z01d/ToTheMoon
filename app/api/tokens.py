from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import TokenStatus
from app.schemas.token import TokenCreate, TokenOut
from app.services.tokens import ensure_token, fetch_token, fetch_tokens


router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("/", response_model=list[TokenOut])
async def list_tokens_endpoint(
    status: Optional[TokenStatus] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    tokens = await fetch_tokens(session, status=status, limit=limit, offset=offset)
    return [TokenOut.model_validate(t) for t in tokens]


@router.get("/{address}", response_model=TokenOut)
async def get_token_endpoint(address: str, session: AsyncSession = Depends(get_session)):
    token = await fetch_token(session, address=address)
    if not token:
        raise HTTPException(status_code=404, detail="token not found")
    return TokenOut.model_validate(token)


@router.post("/dev", response_model=TokenOut)
async def create_token_dev(payload: TokenCreate, session: AsyncSession = Depends(get_session)):
    token = await ensure_token(session, address=payload.address, symbol=payload.symbol)
    return TokenOut.model_validate(token)

