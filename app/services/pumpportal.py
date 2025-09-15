from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.tokens import ensure_token

logger = logging.getLogger("app.services.pumpportal")


async def _handle_message(payload: Any) -> Optional[str]:
    """Extract token address from incoming message.

    Tries common keys used by feeds: 'address', 'mint', 'tokenAddress'.
    Returns the address if found, else None.
    """
    try:
        if isinstance(payload, str):
            # try parse json if stringified
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            return None
    except Exception:
        return None

    for key in ("address", "mint", "tokenAddress"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val
    # Sometimes nested
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        for key in ("address", "mint", "tokenAddress"):
            val = data.get(key)
            if isinstance(val, str) and val:
                return val
    return None


async def run_listener(stop_event: asyncio.Event | None = None) -> None:
    """Run PumpPortal WebSocket listener with reconnect/backoff.

    Creates tokens in DB (status=Initial) when a new token address is observed.
    """
    if not settings.PUMPPORTAL_ENABLED:
        logger.info("pumpportal.disabled")
        return

    url = settings.PUMPPORTAL_WS_URL
    base = 1.0
    cap = 30.0
    attempt = 0

    while True:
        if stop_event and stop_event.is_set():
            logger.info("pumpportal.stop_requested")
            return
        try:
            async with aiohttp.ClientSession() as session:
                logger.info("pumpportal.connecting", extra={"url": url})
                async with session.ws_connect(url, heartbeat=30, timeout=30) as ws:
                    logger.info("pumpportal.connected", extra={"url": url})
                    attempt = 0
                    # Subscribe to migration stream
                    try:
                        await ws.send_str("subscribeMigration")
                        logger.info("pumpportal.subscribed", extra={"channel": "subscribeMigration"})
                    except Exception as e:
                        logger.warning("pumpportal.subscribe_failed %s", e)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            addr = await _handle_message(msg.data)
                            if addr:
                                # Create token if not exists
                                async with SessionLocal() as db:  # type: AsyncSession
                                    await ensure_token(db, address=addr)
                                    # ensure_token commits internally
                                logger.info("pumpportal.token_ingested", extra={"address": addr})
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.warning("pumpportal.ws_closed")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error("pumpportal.ws_error %s", ws.exception())
                            break
        except Exception as e:
            attempt += 1
            delay = min(base * (2 ** (attempt - 1)), cap) + random.random()
            logger.warning("pumpportal.reconnect_in", extra={"sec": round(delay, 1), "error": str(e)})
            try:
                await asyncio.wait_for(asyncio.sleep(delay), timeout=delay + 1)
            except asyncio.CancelledError:
                return

