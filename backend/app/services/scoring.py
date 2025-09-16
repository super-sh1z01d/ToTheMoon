import asyncio
import logging
import os
import math
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx
from sqlmodel import Session, select

from ..db import engine
from ..models.models import Token, TokenMetricHistory, ScoringParameter, Pool
from ..config import DEFAULT_WEIGHTS, DEX_PROGRAM_MAP, ALLOWED_POOL_PROGRAMS
from .market_data import fetch_token_markets, aggregate_filtered_market_metrics
from .pools import _filter_pairs_by_program
from .markets.dexscreener import fetch_pairs as ds_fetch_pairs
from .markets.jupiter import list_programs_for_token

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
                            # 1. Get token overview (for liquidity, name, holders) - BIRDEYE
                            overview_response = await client.get(f"{BIRDEYE_API_URL}{token.token_address}", headers=headers)
                            overview_response.raise_for_status()
                            overview_data = overview_response.json()

                            if not (overview_data.get("success") and overview_data.get("data")):
                                logger.warning(f"No overview data from Birdeye for {token.token_address}")
                                continue
                            
                            overview = overview_data["data"]
                            holder_count = overview.get("holder") or overview.get("holders", 0)
                            logger.info(f"Birdeye data for {token.token_address}: HolderCount={holder_count}")

                            # 2. Get aggregated trade data - BIRDEYE
                            trade_data_response = await client.get(
                                f"{BIRDEYE_TRADE_DATA_URL}{token.token_address}", headers=headers
                            )
                            trade_data_response.raise_for_status()
                            trade_data = trade_data_response.json()

                            if not (trade_data.get("success") and trade_data.get("data")):
                                logger.warning(f"No trade data from Birdeye for {token.token_address}")
                                continue

                            trade_info = trade_data["data"]
                            tx_5m = (
                                trade_info.get("trade_5m")
                                or (trade_info.get("trade_1m") or 0) * 5
                                or (trade_info.get("trade_30m") or 0) / 6
                            )
                            vol_5m = (
                                trade_info.get("volume_5m")
                                or (trade_info.get("volume_1m") or 0.0) * 5
                                or (trade_info.get("volume_30m") or 0.0) / 6
                            )
                            buy_5m = (
                                trade_info.get("volume_buy_5m")
                                or (trade_info.get("volume_buy_1m") or 0.0) * 5
                                or (trade_info.get("volume_buy_30m") or 0.0) / 6
                            )
                            sell_5m = (
                                trade_info.get("volume_sell_5m")
                                or (trade_info.get("volume_sell_1m") or 0.0) * 5
                                or (trade_info.get("volume_sell_30m") or 0.0) / 6
                            )
                            tx_1h = trade_info.get("trade_1h")
                            if tx_1h is None:
                                tx_1h = (trade_info.get("trade_30m") or 0) * 2
                                if tx_1h == 0:
                                    tx_1h = (trade_info.get("trade_5m") or 0) * 12
                            vol_1h = trade_info.get("volume_1h")
                            if vol_1h is None:
                                vol_1h = (trade_info.get("volume_30m") or 0.0) * 2
                                if vol_1h == 0:
                                    vol_1h = (trade_info.get("volume_5m") or 0.0) * 12

                            # 3. Store latest Birdeye metrics in history
                            new_metric = TokenMetricHistory(
                                token_id=token.id,
                                tx_count=int(tx_5m or 0),
                                volume=float(vol_5m or 0.0),
                                holder_count=holder_count,
                                buys_volume=float(buy_5m or 0.0),
                                sells_volume=float(sell_5m or 0.0),
                            )
                            session.add(new_metric)

                            # 4. Fetch historical data for holder growth calculation
                            one_hour_ago_ts = datetime.utcnow() - timedelta(hours=1)
                            historical_metric = session.exec(
                                select(TokenMetricHistory)
                                .where(TokenMetricHistory.token_id == token.id)
                                .where(TokenMetricHistory.timestamp <= one_hour_ago_ts)
                                .order_by(TokenMetricHistory.timestamp.desc())
                            ).first()

                            # 5. Calculate score components using Birdeye data
                            avg_5m_trades = (tx_1h or 0) / 12 if tx_1h else 0
                            tx_accel = (tx_5m / avg_5m_trades) if avg_5m_trades else 0

                            avg_5m_vol = (vol_1h or 0.0) / 12 if vol_1h else 0.0
                            vol_momentum = (vol_5m / avg_5m_vol) if avg_5m_vol else 0

                            holder_now = holder_count or 0
                            holder_1h_ago = historical_metric.holder_count if historical_metric else None
                            
                            if holder_1h_ago is not None and holder_1h_ago > 0:
                                ratio = (holder_now - holder_1h_ago) / holder_1h_ago
                                if ratio <= -0.999999: ratio = -0.999999
                                holder_growth = math.log(1 + ratio)
                            else:
                                holder_growth = 0

                            total_flow = (buy_5m or 0.0) + (sell_5m or 0.0)
                            orderflow_imbalance = ((buy_5m - sell_5m) / total_flow) if total_flow > 0 else 0

                            # 6. Calculate raw and smoothed score
                            raw_score = (
                                weights["W_tx"] * tx_accel +
                                weights["W_vol"] * vol_momentum +
                                weights["W_hld"] * holder_growth +
                                weights["W_oi"] * orderflow_imbalance
                            )
                            smoothed_score = calculate_ewma(raw_score, token.last_smoothed_score, weights["EWMA_ALPHA"])

                            # 7. Deactivation Check 1: Low Score (from Birdeye data)
                            min_score_threshold = weights.get("MIN_SCORE_THRESHOLD", DEFAULT_WEIGHTS["MIN_SCORE_THRESHOLD"])
                            min_score_duration_hours = weights.get("MIN_SCORE_DURATION_HOURS", DEFAULT_WEIGHTS["MIN_SCORE_DURATION_HOURS"])

                            if smoothed_score < min_score_threshold:
                                if token.low_score_since is None:
                                    token.low_score_since = datetime.utcnow()
                                    logger.info(f"Token {token.token_address} score ({smoothed_score:.4f}) below threshold. Starting timer.")
                                elif datetime.utcnow() - token.low_score_since > timedelta(hours=min_score_duration_hours):
                                    token.status = "Initial"
                                    token.low_score_since = None
                                    token.low_activity_streak = 0
                                    logger.info(f"Token {token.token_address} moved to Initial due to prolonged low score.")
                            else:
                                if token.low_score_since is not None:
                                    token.low_score_since = None
                                    logger.info(f"Token {token.token_address} score recovered. Resetting low score timer.")

                            # 8. Deactivation Check 2: Low Pool Activity (from DexScreener data)
                            if token.status == "Active":
                                # Fetch, filter, and update pools in DB
                                ds_data = await ds_fetch_pairs(token.token_address)
                                ds_pairs = ds_data.get("pairs") or []
                                present_programs = await list_programs_for_token(token.token_address)
                                good_pools = _filter_pairs_by_program(ds_pairs, present_programs)

                                # Update DB with the latest valid pools
                                for p in good_pools:
                                    pool_addr = p.get("pairAddress") or p.get("address")
                                    dex_name = p.get("dexId") or ""
                                    if not pool_addr: continue
                                    existing = session.exec(select(Pool).where(Pool.pool_address == pool_addr)).first()
                                    if not existing:
                                        session.add(Pool(pool_address=pool_addr, dex_name=dex_name, token_id=token.id))

                                # Check for inactive pools
                                min_tx_count_deactivate = weights.get("MIN_TX_COUNT", DEFAULT_WEIGHTS["MIN_TX_COUNT"])
                                low_activity_streak_limit = weights.get("LOW_ACTIVITY_STREAK_LIMIT", DEFAULT_WEIGHTS["LOW_ACTIVITY_STREAK_LIMIT"])
                                is_any_pool_inactive = False
                                if not good_pools: # If no valid pools found, consider it inactive
                                    is_any_pool_inactive = True
                                else:
                                    for p in good_pools:
                                        txns_h1 = p.get("txns", {}).get("h1", {})
                                        h1_tx_count = (txns_h1.get("buys", 0) + txns_h1.get("sells", 0))
                                        if h1_tx_count < min_tx_count_deactivate:
                                            is_any_pool_inactive = True
                                            break # Found one inactive pool, no need to check others
                                
                                if is_any_pool_inactive:
                                    token.low_activity_streak += 1
                                    logger.info(f"Token {token.token_address} has low pool activity. Streak: {token.low_activity_streak}/{low_activity_streak_limit}")
                                    if token.low_activity_streak >= low_activity_streak_limit:
                                        token.status = "Initial"
                                        token.low_activity_streak = 0
                                        token.low_score_since = None
                                        logger.info(f"Token {token.token_address} moved to Initial due to prolonged low pool activity.")
                                else:
                                    if token.low_activity_streak > 0:
                                        logger.info(f"Token {token.token_address} pool activity recovered. Resetting streak.")
                                        token.low_activity_streak = 0

                            # 9. Finalize token update
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
