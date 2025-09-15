from __future__ import annotations

from typing import Iterable, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token, TokenStatus


async def list_tokens(
    session: AsyncSession,
    *,
    status: Optional[TokenStatus] = None,
    limit: int = 100,
    offset: int = 0,
) -> Iterable[Token]:
    stmt = select(Token).order_by(Token.id.desc()).limit(limit).offset(offset)
    if status is not None:
        stmt = stmt.filter(Token.status == status)
    res = await session.execute(stmt)
    return res.scalars().all()


async def get_by_address(session: AsyncSession, address: str) -> Optional[Token]:
    res = await session.execute(select(Token).where(Token.address == address))
    return res.scalars().first()


async def create_if_not_exists(
    session: AsyncSession,
    *,
    address: str,
    symbol: Optional[str] = None,
) -> Token:
    existing = await get_by_address(session, address)
    if existing:
        return existing
    token = Token(
        address=address,
        symbol=symbol,
        status=TokenStatus.INITIAL,
        created_at=datetime.now(timezone.utc),
        activated_at=None,
        last_score_value=None,
    )
    session.add(token)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
    # fetch again to return with id
    existing = await get_by_address(session, address)
    assert existing is not None
    return existing

