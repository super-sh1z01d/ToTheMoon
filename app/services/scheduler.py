from __future__ import annotations

import asyncio
import logging
from typing import Iterable, Dict
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.token import Token, TokenStatus
from app.models.score import TokenScore
from app.models.snapshots import TokenSnapshot, PoolSnapshot
from app.repositories.token import list_tokens, update_status
from app.services import birdeye
from app.services.scoring import compute_and_store_score, load_weights

logger = logging.getLogger("app.services.scheduler")


async def _activate_initial_tokens(batch: int = 50) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        tokens: Iterable[Token] = await list_tokens(session, status=TokenStatus.INITIAL, limit=batch)
        for t in tokens:
            try:
                data = await birdeye.token_overview(t.address)
            except Exception as e:
                logger.warning("scheduler.initial.check_failed", extra={"address": t.address, "error": str(e)})
                continue
            if _meets_activation_criteria(data):
                await update_status(session, token=t, status=TokenStatus.ACTIVE)
                logger.info("scheduler.initial.activated", extra={"address": t.address})


def _meets_activation_criteria(data: dict) -> bool:
    # Heuristic: activate if liquidity is present and above threshold, or if pools/pairs present.
    try:
        d = data.get("data", data)
        if isinstance(d, dict):
            liq = d.get("liquidity") or d.get("liquidityUSD") or d.get("liquidity_usd")
            try:
                if liq is not None and float(liq) >= settings.MIN_ACTIVE_LIQUIDITY:
                    return True
            except Exception:
                pass
            for key in ("pools", "pairs"):
                val = d.get(key)
                if isinstance(val, list) and len(val) > 0:
                    return True
        return bool(d)
    except Exception:
        return False


async def run_scheduler(stop_event: asyncio.Event | None = None) -> None:
    if stop_event is None:
        stop_event = asyncio.Event()
    logger.info("scheduler.started")
    while not stop_event.is_set():
        try:
            await _activate_initial_tokens()
        except Exception as e:
            logger.error("scheduler.initial.error", extra={"error": str(e)})
        await asyncio.sleep(settings.SCHED_INTERVAL_INITIAL_SEC)

        # Score active tokens
        try:
            async with SessionLocal() as session:  # type: AsyncSession
                active_tokens: Iterable[Token] = await list_tokens(
                    session, status=TokenStatus.ACTIVE, limit=50
                )
                weights = await load_weights(session)
                # streak of low scores in-memory
                for t in active_tokens:
                    try:
                        overview = await birdeye.token_overview(t.address)
                        score, _ = await compute_and_store_score(
                            session, token=t, overview=overview, weights=weights
                        )
                        # degrade if score below threshold for N checks
                        if score < settings.MIN_SCORE_KEEP_ACTIVE:
                            _LOW_SCORE_STREAK[t.id] = _LOW_SCORE_STREAK.get(t.id, 0) + 1
                            if _LOW_SCORE_STREAK[t.id] >= settings.DEGRADE_CHECKS:
                                await update_status(session, token=t, status=TokenStatus.ARCHIVED)
                                _LOW_SCORE_STREAK.pop(t.id, None)
                                logger.info("scheduler.degrade.archived", extra={"address": t.address})
                        else:
                            _LOW_SCORE_STREAK.pop(t.id, None)
                    except Exception as e:
                        logger.warning("scheduler.active.score_failed", extra={"address": t.address, "error": str(e)})
        except Exception as e:
            logger.error("scheduler.active.error", extra={"error": str(e)})

        # Periodic cleanup once per hour
        try:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=2)
            async with SessionLocal() as session:  # type: AsyncSession
                await session.execute(delete(TokenScore).where(TokenScore.ts < cutoff))
                await session.execute(delete(TokenSnapshot).where(TokenSnapshot.ts < cutoff))
                await session.execute(delete(PoolSnapshot).where(PoolSnapshot.ts < cutoff))
                await session.commit()
        except Exception as e:
            logger.warning("scheduler.cleanup.failed", extra={"error": str(e)})


# in-memory streak tracking for low scores
_LOW_SCORE_STREAK: Dict[int, int] = {}
