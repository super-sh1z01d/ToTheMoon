from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token, TokenStatus
from app.repositories.token import create_if_not_exists, get_by_address, list_tokens


async def ensure_token(session: AsyncSession, *, address: str, symbol: Optional[str] = None) -> Token:
    return await create_if_not_exists(session, address=address, symbol=symbol)


async def fetch_token(session: AsyncSession, *, address: str) -> Optional[Token]:
    return await get_by_address(session, address)


async def fetch_tokens(
    session: AsyncSession, *, status: Optional[TokenStatus] = None, limit: int = 100, offset: int = 0
):
    return await list_tokens(session, status=status, limit=limit, offset=offset)

