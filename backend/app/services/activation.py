import asyncio
import logging
import os
from datetime import datetime, timedelta

import httpx
from sqlmodel import Session, select

from ..db import engine
from ..models.models import Token, ScoringParameter # Import ScoringParameter
from .scoring import get_scoring_weights # Import from scoring
from ..config import DEFAULT_WEIGHTS # Import from config

logger = logging.getLogger(__name__)

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/token_overview?address="

# Activation criteria from functional_task.md
MIN_LIQUIDITY_USD = 500
MIN_TX_COUNT = 300
ARCHIVE_TIMEDELTA = timedelta(hours=24)

async def activate_tokens():
    """
    Periodically checks tokens with 'Initial' status and updates them to
    'Active' or 'Archived' based on defined criteria.
    """
    if not BIRDEYE_API_KEY:
        logger.error("BIRDEYE_API_KEY is not set. Birdeye API calls will fail.")
        await asyncio.sleep(60) # Sleep to prevent tight loop if API key is missing
        return

    while True:
        with Session(engine) as session:
            weights = get_scoring_weights(session) # Use get_scoring_weights
            polling_interval = weights.get("POLLING_INTERVAL_INITIAL", DEFAULT_WEIGHTS["POLLING_INTERVAL_INITIAL"])

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

                headers = {"X-API-KEY": BIRDEYE_API_KEY}
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
                            response = await client.get(f"{BIRDEYE_API_URL}{token.token_address}", headers=headers)
                            response.raise_for_status() # Raise exception for 4xx or 5xx responses
                            data = response.json()

                            if data.get("success") and data.get("data"):
                                overview = data["data"]
                                liquidity = overview.get("liquidity", 0)
                                tx_count_24h = overview.get("txns24h", {}).get("v", 0) # Assuming we use 24h tx count

                                if liquidity >= MIN_LIQUIDITY_USD and tx_count_24h >= MIN_TX_COUNT:
                                    token.status = "Active"
                                    token.activated_at = datetime.utcnow()
                                    token.name = overview.get("name") # Save the token name
                                    logger.info(f"Activating token {token.token_address} ({token.name})")
                                    session.add(token)
                        except httpx.HTTPStatusError as e:
                            logger.error(f"HTTP error fetching data for {token.token_address}: {e}")
                        except Exception as e:
                            logger.error(f"Error processing token {token.token_address}: {e}")

                session.commit()
            except Exception as e:
                logger.error(f"An error occurred in the activation loop: {e}")
        await asyncio.sleep(polling_interval) # Sleep after processing all tokens
