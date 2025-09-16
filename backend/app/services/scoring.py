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
from ..config import DEFAULT_WEIGHTS  # Import from config
from ..config import EXCLUDED_POOL_PROGRAMS
from .market_data import fetch_token_markets, aggregate_filtered_market_metrics
from ..config import EXCLUDED_DEX_IDS
from .markets.dexscreener import fetch_pairs as ds_fetch_pairs, aggregate_allowed_pairs as ds_aggregate

logger = logging.getLogger(__name__)

BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/token_overview?address="
BIRDEYE_TRADE_DATA_URL = "https://public-api.birdeye.so/defi/v3/token/trade-data/single?address="

def get_scoring_weights(session: Session) -> Dict[str, float]:
    """Fetches scoring weights from the database, using defaults if not found."""
    weights = DEFAULT_WEIGHTS.copy()
    params = session.exec(select(ScoringParameter)).all()
    for p in params:
        weights[p.param_name] = p.param_value # Use param_value directly, it can be float or int
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
    api_key = os.getenv("BIRDEYE_API_KEY")
    if not api_key:
        logger.error("BIRDEYE_API_KEY is not set. Birdeye API calls will fail.")
        await asyncio.sleep(60)  # Sleep to prevent tight loop if API key is missing
        return

    while True:
        with Session(engine) as session:
            weights = get_scoring_weights(session)
            polling_interval = weights.get("POLLING_INTERVAL_ACTIVE", DEFAULT_WEIGHTS["POLLING_INTERVAL_ACTIVE"])

            if polling_interval == 0:
                logger.info("Polling for active tokens is disabled.")
                await asyncio.sleep(60) # Sleep for a default time if disabled to avoid tight loop
                continue

            logger.info(f"Running token scoring process (interval: {polling_interval}s)...")

            try:
                active_tokens = session.exec(select(Token).where(Token.status == "Active")).all()

                if not active_tokens:
                    logger.info("No active tokens to score.")
                    await asyncio.sleep(polling_interval) # Sleep even if no tokens
                    continue

                headers = {
                    "X-API-KEY": api_key,
                    "x-chain": "solana",
                    "accept": "application/json",
                }
                async with httpx.AsyncClient() as client:
                    for token in active_tokens:
                        try:
                            # 1. Get token overview (for liquidity, name, holders)
                            overview_response = await client.get(f"{BIRDEYE_API_URL}{token.token_address}", headers=headers)
                            overview_response.raise_for_status()
                            overview_data = overview_response.json()

                            if not (overview_data.get("success") and overview_data.get("data")):
                                logger.warning(f"No overview data from Birdeye for {token.token_address}")
                                continue
                            
                            overview = overview_data["data"]
                            # Birdeye overview uses 'holder' key; keep fallback to 'holders'
                            holder_count = overview.get("holder") or overview.get("holders", 0)
                            logger.info(f"Birdeye data for {token.token_address}: HolderCount={holder_count}")

                            # Prefer DexScreener aggregated per-market metrics excluding Bonding Curve
                            ds = await ds_fetch_pairs(token.token_address)
                            agg = ds_aggregate(ds, EXCLUDED_DEX_IDS)
                            tx_5m = float(agg.get("trade_5m") or 0)
                            vol_5m = float(agg.get("volume_5m") or 0.0)
                            buy_count_5m = float(agg.get("buy_count_5m") or 0)
                            sell_count_5m = float(agg.get("sell_count_5m") or 0)
                            tx_1h = float(agg.get("trade_1h") or 0)
                            vol_1h = float(agg.get("volume_1h") or 0.0)

                            # Store snapshot metrics into history (5m window)
                            tx_count = int(tx_5m or 0)
                            volume = float(vol_5m or 0.0)
                            # Use counts as proxy for orderflow (DexScreener doesn't expose buy/sell volume per 5m)
                            buys_volume = float(buy_count_5m or 0.0)
                            sells_volume = float(sell_count_5m or 0.0)

                            # 2. Store latest metrics in history
                            new_metric = TokenMetricHistory(
                                token_id=token.id,
                                tx_count=tx_count,
                                volume=volume,
                                holder_count=holder_count,
                                buys_volume=buys_volume,
                                sells_volume=sells_volume,
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

                            # We can score even with a single prior point for holder growth fallback
                            has_two_points = len(history) >= 2

                            # 4. Calculate score components using 5m/1h windows (per spec)
                            # Tx_Accel: current 5m vs average 5m over 1h
                            avg_5m_trades = (tx_1h or 0) / 12 if tx_1h else 0
                            tx_accel = (tx_5m / avg_5m_trades) if avg_5m_trades else 0

                            # Vol_Momentum: volume_5m vs avg 5m over 1h
                            avg_5m_vol = (vol_1h or 0.0) / 12 if vol_1h else 0.0
                            vol_momentum = (vol_5m / avg_5m_vol) if avg_5m_vol else 0

                            # Holder_Growth: log(1 + (holders_now - holders_1h_ago)/holders_1h_ago)
                            holder_now = holder_count or 0
                            holder_1h_ago = None
                            if history:
                                holder_1h_ago = history[-1].holder_count
                            if holder_1h_ago and holder_1h_ago > 0:
                                ratio = (holder_now - holder_1h_ago) / holder_1h_ago
                                # Prevent log(0) or negative domain
                                if ratio <= -0.999999:
                                    ratio = -0.999999
                                holder_growth = math.log(1 + ratio)
                            else:
                                holder_growth = 0

                            # Orderflow_Imbalance: use counts as proxy
                            total_flow = buy_count_5m + sell_count_5m
                            orderflow_imbalance = ((buy_count_5m - sell_count_5m) / total_flow) if total_flow > 0 else 0

                            # 5. Calculate raw score
                            raw_score = (
                                weights["W_tx"] * tx_accel +
                                weights["W_vol"] * vol_momentum +
                                weights["W_hld"] * holder_growth +
                                weights["W_oi"] * orderflow_imbalance
                            )

                            # 6. Apply EWMA smoothing and update token
                            smoothed_score = calculate_ewma(raw_score, token.last_smoothed_score, weights["EWMA_ALPHA"])

                            # Check for low score condition
                            min_score_threshold = weights.get("MIN_SCORE_THRESHOLD", DEFAULT_WEIGHTS["MIN_SCORE_THRESHOLD"])
                            min_score_duration_hours = weights.get("MIN_SCORE_DURATION_HOURS", DEFAULT_WEIGHTS["MIN_SCORE_DURATION_HOURS"])

                            if smoothed_score < min_score_threshold:
                                if token.low_score_since is None:
                                    token.low_score_since = datetime.utcnow()
                                    logger.info(f"Token {token.token_address} score ({smoothed_score:.4f}) fell below threshold ({min_score_threshold:.4f}). Starting low score timer.")
                                elif datetime.utcnow() - token.low_score_since > timedelta(hours=min_score_duration_hours):
                                    token.status = "Initial"
                                    token.low_score_since = None # Reset timer
                                    logger.info(f"Token {token.token_address} moved to Initial due to prolonged low score.")
                            else:
                                if token.low_score_since is not None:
                                    token.low_score_since = None # Reset timer
                                    logger.info(f"Token {token.token_address} score recovered. Resetting low score timer.")

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
        await asyncio.sleep(polling_interval) # Sleep after processing all tokens
