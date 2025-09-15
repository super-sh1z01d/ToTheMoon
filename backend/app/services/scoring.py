import asyncio
import logging
import os
import math
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx
from sqlmodel import Session, select

from ..db import engine
from ..models.models import Token, TokenMetricHistory, ScoringParameter

logger = logging.getLogger(__name__)

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/token_overview?address="

# Default scoring weights
DEFAULT_WEIGHTS = {
    "W_tx": 0.25,
    "W_vol": 0.25,
    "W_hld": 0.25,
    "W_oi": 0.25,
    "EWMA_ALPHA": 0.3, # Smoothing factor
}

def get_scoring_weights(session: Session) -> Dict[str, float]:
    """Fetches scoring weights from the database, using defaults if not found."""
    weights = DEFAULT_WEIGHTS.copy()
    params = session.exec(select(ScoringParameter)).all()
    for p in params:
        if p.param_name in weights:
            weights[p.param_name] = p.param_value
    return weights

def calculate_ewma(current_value: float, prev_ewma: Optional[float], alpha: float) -> float:
    """Calculates the Exponentially Weighted Moving Average."""
    if prev_ewma is None:
        return current_value
    return alpha * current_value + (1 - alpha) * prev_ewma

async def score_tokens():
    """
    Periodically calculates scores for active tokens.
    """
    while True:
        await asyncio.sleep(300) # Run every 5 minutes
        logger.info("Running token scoring process...")

        with Session(engine) as session:
            try:
                weights = get_scoring_weights(session)
                active_tokens = session.exec(select(Token).where(Token.status == "Active")).all()

                if not active_tokens:
                    logger.info("No active tokens to score.")
                    continue

                headers = {"X-API-KEY": BIRDEYE_API_KEY}
                async with httpx.AsyncClient() as client:
                    for token in active_tokens:
                        try:
                            # 1. Fetch latest data from Birdeye
                            response = await client.get(f"{BIRDEYE_API_URL}{token.token_address}", headers=headers)
                            response.raise_for_status()
                            data = response.json()

                            if not (data.get("success") and data.get("data")):
                                logger.warning(f"No data from Birdeye for {token.token_address}")
                                continue

                            overview = data["data"]
                            # 2. Store latest metrics in history
                            new_metric = TokenMetricHistory(
                                token_id=token.id,
                                tx_count=overview.get("txns24h", {}).get("v", 0),
                                volume=overview.get("volume24h", 0),
                                holder_count=overview.get("holders", 0),
                                buys_volume=overview.get("volume24hBuy", 0),
                                sells_volume=overview.get("volume24hSell", 0),
                            )
                            session.add(new_metric)

                            # 3. Fetch historical data for calculations (last hour)
                            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                            history = session.exec(
                                select(TokenMetricHistory)
                                .where(TokenMetricHistory.token_id == token.id)
                                .where(TokenMetricHistory.timestamp >= one_hour_ago)
                                .order_by(TokenMetricHistory.timestamp.desc())
                            ).all()

                            if len(history) < 2: # Need at least 2 data points
                                logger.info(f"Not enough historical data to score {token.token_address}")
                                continue

                            # 4. Calculate score components (simplified for now)
                            # In a real scenario, you'd compare 5m vs 1h data.
                            # Here we simulate it by comparing the latest two data points.
                            latest = history[0]
                            previous = history[-1]

                            tx_accel = (latest.tx_count - previous.tx_count) / (len(history) or 1)
                            vol_momentum = (latest.volume - previous.volume) / (len(history) or 1)
                            holder_growth = math.log(1 + (latest.holder_count - previous.holder_count)) if previous.holder_count > 0 else 0
                            total_flow = latest.buys_volume + latest.sells_volume
                            orderflow_imbalance = (latest.buys_volume - latest.sells_volume) / total_flow if total_flow > 0 else 0

                            # 5. Calculate raw score
                            raw_score = (
                                weights["W_tx"] * tx_accel +
                                weights["W_vol"] * vol_momentum +
                                weights["W_hld"] * holder_growth +
                                weights["W_oi"] * orderflow_imbalance
                            )

                            # 6. Apply EWMA smoothing and update token
                            smoothed_score = calculate_ewma(raw_score, token.last_smoothed_score, weights["EWMA_ALPHA"])
                            token.last_score_value = raw_score
                            token.last_smoothed_score = smoothed_score
                            token.last_updated = datetime.utcnow()
                            session.add(token)
                            logger.info(f"Scored token {token.token_address}: {smoothed_score:.4f}")

                        except Exception as e:
                            logger.error(f"Error scoring token {token.token_address}: {e}")

                session.commit()
            except Exception as e:
                logger.error(f"An error occurred in the scoring loop: {e}")
