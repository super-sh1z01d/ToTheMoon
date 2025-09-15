from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.score import TokenScore
from app.models.token import Token
from app.repositories.settings import get_setting
from app.schemas.settings import ScoringSettings


@dataclass
class Weights:
    tx_accel: float = 0.25
    vol_momentum: float = 0.25
    holder_growth: float = 0.25
    orderflow_imbalance: float = 0.25


def _extract_metrics(overview: Dict[str, Any]) -> Dict[str, float]:
    d = overview.get("data", overview)
    metrics: Dict[str, float] = {}
    # Best-effort extraction; default to 0.0 if missing
    metrics["tx_count_5m"] = float(d.get("tx_count_5m", 0) or 0)
    metrics["tx_count_1h"] = float(d.get("tx_count_1h", 0) or 0)
    metrics["volume_5m"] = float(d.get("volume_5m", 0) or 0)
    metrics["volume_1h"] = float(d.get("volume_1h", 0) or 0)
    metrics["holders_now"] = float(d.get("holders", 0) or 0)
    metrics["holders_1h_ago"] = float(d.get("holders_1h_ago", metrics["holders_now"]))
    metrics["buys_volume_5m"] = float(d.get("buys_volume_5m", 0) or 0)
    metrics["sells_volume_5m"] = float(d.get("sells_volume_5m", 0) or 0)
    return metrics


def _compute_components(m: Dict[str, float]) -> Dict[str, float]:
    def safe_div(a: float, b: float) -> float:
        return a / b if b else 0.0

    tx_accel = safe_div(m["tx_count_5m"] / 5.0, m["tx_count_1h"] / 60.0)
    vol_momentum = safe_div(m["volume_5m"], m["volume_1h"] / 12.0)
    # holder growth stabilized
    delta_h = max(m["holders_now"] - m["holders_1h_ago"], 0.0)
    holder_growth = 0.0
    if m["holders_1h_ago"] > 0:
        holder_growth = __import__("math").log(1 + (delta_h / m["holders_1h_ago"]))
    orderflow_imbalance = safe_div(m["buys_volume_5m"] - m["sells_volume_5m"], m["buys_volume_5m"] + m["sells_volume_5m"])

    return {
        "Tx_Accel": max(tx_accel, 0.0),
        "Vol_Momentum": max(vol_momentum, 0.0),
        "Holder_Growth": max(holder_growth, 0.0),
        "Orderflow_Imbalance": orderflow_imbalance,
    }


def _weighted_sum(components: Dict[str, float], w: Weights) -> float:
    return (
        components["Tx_Accel"] * w.tx_accel
        + components["Vol_Momentum"] * w.vol_momentum
        + components["Holder_Growth"] * w.holder_growth
        + components["Orderflow_Imbalance"] * w.orderflow_imbalance
    )


async def compute_and_store_score(
    session: AsyncSession,
    *,
    token: Token,
    overview: Dict[str, Any],
    weights: Weights | None = None,
    alpha: float | None = None,
) -> Tuple[float, Dict[str, float]]:
    weights = weights or Weights()
    metrics = _extract_metrics(overview)
    components = _compute_components(metrics)
    raw_score = _weighted_sum(components, weights)
    prev = token.last_score_value or 0.0
    alpha = alpha if alpha is not None else settings.SCORING_ALPHA
    ewma = alpha * raw_score + (1 - alpha) * prev

    ts = datetime.now(timezone.utc)
    row = TokenScore(token_id=token.id, ts=ts, score=ewma, components={"raw": raw_score, **components})
    session.add(row)
    token.last_score_value = ewma
    await session.commit()
    return ewma, components


async def load_weights(session: AsyncSession) -> Weights:
    cfg = await get_setting(session, "scoring")
    if not cfg:
        return Weights()
    w = cfg.get("weights", {})
    try:
        return Weights(
            tx_accel=float(w.get("Tx_Accel", 0.25)),
            vol_momentum=float(w.get("Vol_Momentum", 0.25)),
            holder_growth=float(w.get("Holder_Growth", 0.25)),
            orderflow_imbalance=float(w.get("Orderflow_Imbalance", 0.25)),
        )
    except Exception:
        return Weights()


async def load_scoring_params(session: AsyncSession) -> tuple[Weights, ScoringSettings]:
    cfg = await get_setting(session, "scoring")
    sc = ScoringSettings(**cfg) if cfg else ScoringSettings()
    w = Weights(
        tx_accel=sc.weights.Tx_Accel,
        vol_momentum=sc.weights.Vol_Momentum,
        holder_growth=sc.weights.Holder_Growth,
        orderflow_imbalance=sc.weights.Orderflow_Imbalance,
    )
    return w, sc
