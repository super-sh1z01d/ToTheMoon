import asyncio
import logging
import os
from datetime import datetime, timedelta

import httpx
from sqlmodel import Session, select

from ..db import engine
from ..models.models import Token, ScoringParameter  # Import ScoringParameter
from .scoring import get_scoring_weights  # Import from scoring
from ..config import DEFAULT_WEIGHTS  # Import from config
from .market_data import fetch_token_markets, aggregate_filtered_market_metrics
from ..config import EXCLUDED_POOL_PROGRAMS, ALLOWED_POOL_PROGRAMS
from .markets.jupiter import has_allowed_route

logger = logging.getLogger(__name__)

BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/token_overview?address="
BIRDEYE_TRADE_DATA_URL = "https://public-api.birdeye.so/defi/v3/token/trade-data/single?address="

ARCHIVE_TIMEDELTA = timedelta(hours=24) # Re-added this constant

async def activate_tokens():
    """
    Periodically checks tokens with 'Initial' status and updates them to
    'Active' or 'Archived' based on defined criteria.
    """
    from .scoring import get_scoring_weights  # Import from scoring
    from .pools import update_token_pools

    api_key = os.getenv("BIRDEYE_API_KEY")
    if not api_key:
        logger.error("BIRDEYE_API_KEY is not set. Birdeye API calls will fail.")
        await asyncio.sleep(60)  # Sleep to prevent tight loop if API key is missing
        return

    while True:
        with Session(engine) as session:
            weights = get_scoring_weights(session) # Use get_scoring_weights
            polling_interval = weights.get("POLLING_INTERVAL_INITIAL", DEFAULT_WEIGHTS["POLLING_INTERVAL_INITIAL"])
            min_liquidity_usd = weights.get("MIN_LIQUIDITY_USD", DEFAULT_WEIGHTS["MIN_LIQUIDITY_USD"])
            min_tx_count = weights.get("MIN_TX_COUNT", DEFAULT_WEIGHTS["MIN_TX_COUNT"])

            if polling_interval == 0:
                logger.info("Polling for initial tokens is disabled.")
                await asyncio.sleep(60) # Sleep for a default time if disabled to avoid tight loop
                continue

            logger.info(f"Running token activation check (interval: {polling_interval}s)...")

            try:
                initial_tokens = session.exec(select(Token).where(Token.status == "Initial")).all()
                if not initial_tokens:
                    logger.info("No initial tokens to process.")
                    await asyncio.sleep(polling_interval) # Sleep even if no tokens
                    continue

                headers = {
                    "X-API-KEY": api_key,
                    "x-chain": "solana",
                    "accept": "application/json",
                }
                async with httpx.AsyncClient() as client:
                    for token in initial_tokens:
                        # Check for archival
                        if datetime.utcnow() - token.created_at > ARCHIVE_TIMEDELTA:
                            token.status = "Archived"
                            logger.info(f"Archiving token {token.token_address} due to age.")
                            session.add(token)
                            continue # Move to the next token

                        # Check for activation
                        try:
                            # 1. Get token overview (for liquidity and name)
                            overview_response = await client.get(f"{BIRDEYE_API_URL}{token.token_address}", headers=headers)
                            overview_response.raise_for_status()
                            overview_data = overview_response.json()

                            if not (overview_data.get("success") and overview_data.get("data")):
                                logger.warning(f"No overview data from Birdeye for {token.token_address}")
                                continue
                            
                            overview = overview_data["data"]
                            liquidity = overview.get("liquidity", 0)
                            token_name = overview.get("name")

                            # 2. Get trade data (for total transaction count)
                            trade_data_response = await client.get(
                                f"{BIRDEYE_TRADE_DATA_URL}{token.token_address}", headers=headers
                            )
                            trade_data_response.raise_for_status()
                            trade_data = trade_data_response.json()

                            if not (trade_data.get("success") and trade_data.get("data")):
                                logger.warning(f"No trade data from Birdeye for {token.token_address}")
                                continue

                            trade_info = trade_data["data"]

                            # Use Birdeye trade-data aggregated windows (allowing all markets)
                            tx_1h = trade_info.get("trade_1h")
                            if tx_1h is None:
                                tx30 = trade_info.get("trade_30m")
                                if tx30 is not None:
                                    tx_1h = tx30 * 2
                                else:
                                    tx5 = trade_info.get("trade_5m")
                                    tx_1h = tx5 * 12 if tx5 is not None else 0
                            tx_count_total = int(tx_1h or 0)

                            # Require at least one allowed route (real DEX) via Jupiter
                            try:
                                allowed = await has_allowed_route(token.token_address, ALLOWED_POOL_PROGRAMS)
                            except Exception:
                                allowed = False
                            if not allowed:
                                logger.info(f"No allowed Jupiter route for {token.token_address}; skipping activation.")
                                continue

                            logger.info(f"Birdeye data for {token.token_address}: Liquidity={liquidity}, TotalTxCount={tx_count_total}")

                            if liquidity >= min_liquidity_usd and tx_count_total >= min_tx_count:
                                token.status = "Active"
                                token.activated_at = datetime.utcnow()
                                token.name = token_name # Save the token name
                                logger.info(f"Activating token {token.token_address} ({token.name}) with Liquidity={liquidity}, TotalTxCount={tx_count_total}")
                                session.add(token)
                        except httpx.HTTPStatusError as e:
                            logger.error(f"HTTP error fetching data for {token.token_address}: {e}")
                        except Exception as e:
                            logger.error(f"Error processing token {token.token_address}: {e}")

                session.commit()
            except Exception as e:
                logger.error(f"An error occurred in the activation loop: {e}")
        await asyncio.sleep(polling_interval) # Sleep after processing all tokens
rror fetching data for {token.token_address}: {e}")
                        except Exception as e:
                            logger.error(f"Error processing token {token.token_address}: {e}")

                session.commit()
            except Exception as e:
                logger.error(f"An error occurred in the activation loop: {e}")
        await asyncio.sleep(polling_interval) # Sleep after processing all tokens
