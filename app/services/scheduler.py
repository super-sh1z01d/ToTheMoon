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
from app.services.scoring import compute_and_store_score, load_scoring_params

logger = logging.getLogger("app.services.scheduler")


async def _activate_initial_tokens(batch: int = 50) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        tokens: Iterable[Token] = await list_tokens(session, status=TokenStatus.INITIAL, limit=batch)
        weights, sc = await load_scoring_params(session)
        for t in tokens:
            try:
                data = await birdeye.token_overview(t.address)
            except Exception as e:
                logger.warning("scheduler.initial.check_failed", extra={"address": t.address, "error": str(e)})
                continue
            if _meets_activation_criteria(data, min_liq=sc.min_active_liquidity, min_tx=sc.min_tx_count):
                await update_status(session, token=t, status=TokenStatus.ACTIVE)
                logger.info("scheduler.initial.activated", extra={"address": t.address})


def _meets_activation_criteria(data: dict, *, min_liq: float, min_tx: int) -> bool:
    # Heuristic: activate if liquidity is present and above threshold, or if pools/pairs present.
    try:
        d = data.get("data", data)
        if isinstance(d, dict):
            liq = d.get("liquidity") or d.get("liquidityUSD") or d.get("liquidity_usd")
            try:
                if liq is not None and float(liq) >= float(min_liq):
                    return True
            except Exception:
                pass
            # tx threshold
            tx1h = d.get("tx_count_1h") or 0
            try:
                if float(tx1h) >= float(min_tx):
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
                weights, sc = await load_scoring_params(session)
                # streak of low scores in-memory
                for t in active_tokens:
                    try:
                        overview = await birdeye.token_overview(t.address)
                        score, _ = await compute_and_store_score(
                            session, token=t, overview=overview, weights=weights, alpha=sc.ewma_alpha
                        )
                        # snapshot minimal metrics
                        _store_token_snapshot(session, t.id, overview)
                        # degrade if score below threshold for N checks
                        cond_low_score = score < sc.min_score_keep_active
                        cond_low_tx = _get_tx_count_1h(overview) < sc.min_tx_count
                        if cond_low_score or cond_low_tx:
                            count, first_ts = _LOW_SCORE_STREAK.get(t.id, (0, _now_utc()))
                            # reset window if too old
                            if (_now_utc() - first_ts).total_seconds() > sc.degrade_window_hours * 3600:
                                count = 0
                                first_ts = _now_utc()
                            count += 1
                            _LOW_SCORE_STREAK[t.id] = (count, first_ts)
                            if count >= sc.degrade_checks:
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
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _get_tx_count_1h(overview: dict) -> float:
    d = overview.get("data", overview)
    try:
        return float(d.get("tx_count_1h", 0) or 0)
    except Exception:
        return 0.0


def _store_token_snapshot(session: AsyncSession, token_id: int, overview: dict) -> None:
    d = overview.get("data", overview)
    holders = d.get("holders")
    price = d.get("price_usd", d.get("price"))
    try:
        row = TokenSnapshot(token_id=token_id, ts=_now_utc(), holders=int(holders) if holders is not None else None, price=float(price) if price is not None else None)  # type: ignore[arg-type]
        session.add(row)
    except Exception:
        pass
