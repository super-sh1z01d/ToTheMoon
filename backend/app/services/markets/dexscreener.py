import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEXSCREENER_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/"


async def fetch_pairs(token_address: str) -> Dict[str, Any]:
    url = f"{DEXSCREENER_TOKEN_URL}{token_address}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json() or {}
    except Exception as e:
        logger.debug(f"DexScreener fetch error for {token_address}: {e}")
        return {}


def aggregate_allowed_pairs(
    data: Dict[str, Any],
    excluded_dex_ids: List[str],
) -> Dict[str, float]:
    """
    Aggregate metrics across allowed pairs (exclude dexIds).
    Returns keys: liquidity_usd, trade_5m, volume_5m, buy_count_5m, sell_count_5m, trade_1h, volume_1h
    """
    pairs = data.get("pairs") or []
    if not isinstance(pairs, list):
        pairs = []

    res = {
        "liquidity_usd": 0.0,
        "trade_5m": 0.0,
        "volume_5m": 0.0,
        "buy_count_5m": 0.0,
        "sell_count_5m": 0.0,
        "trade_1h": 0.0,
        "volume_1h": 0.0,
        "allowed_pairs": 0,
        "total_pairs": len(pairs),
    }

    excluded = {d.lower() for d in excluded_dex_ids}

    for p in pairs:
        dex_id = (p.get("dexId") or "").lower()
        if dex_id in excluded:
            continue

        res["allowed_pairs"] += 1

        # liquidity
        liq = p.get("liquidity") or {}
        res["liquidity_usd"] += float(liq.get("usd") or 0.0)

        # volume windows
        vol = p.get("volume") or {}
        res["volume_5m"] += float(vol.get("m5") or 0.0)
        res["volume_1h"] += float(vol.get("h1") or 0.0)

        # transactions windows
        tx = p.get("txns") or {}
        tx_5m = tx.get("m5") or {}
        tx_1h = tx.get("h1") or {}

        buys_5m = int(tx_5m.get("buys") or 0)
        sells_5m = int(tx_5m.get("sells") or 0)
        res["buy_count_5m"] += buys_5m
        res["sell_count_5m"] += sells_5m
        res["trade_5m"] += buys_5m + sells_5m

        res["trade_1h"] += int(tx_1h.get("buys") or 0) + int(tx_1h.get("sells") or 0)

    return res

