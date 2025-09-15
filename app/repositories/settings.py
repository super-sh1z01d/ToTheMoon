from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Setting


async def get_setting(session: AsyncSession, key: str) -> Optional[dict]:
    obj = await session.get(Setting, key)
    return obj.value if obj else None


async def upsert_setting(session: AsyncSession, key: str, value: dict) -> None:
    obj = await session.get(Setting, key)
    now = datetime.now(timezone.utc)
    if obj is None:
        obj = Setting(key=key, value=value, updated_at=now)
        session.add(obj)
    else:
        obj.value = value
        obj.updated_at = now
    await session.commit()

