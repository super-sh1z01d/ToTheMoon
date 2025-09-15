import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


async def fetch_token_markets(
    client: httpx.AsyncClient,
    token_address: str,
    headers: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Try multiple Birdeye endpoints to retrieve per-market/pool data for a token.
    Returns a list of market dicts or empty list if not available on current plan.
    """
    endpoints = [
        f"https://public-api.birdeye.so/defi/v3/token/markets?address={token_address}",
        f"https://public-api.birdeye.so/defi/token_markets?address={token_address}",
        f"https://public-api.birdeye.so/defi/token/markets?address={token_address}",
        f"https://public-api.birdeye.so/defi/v3/amm/markets?address={token_address}",
    ]

    for url in endpoints:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                continue
            data = resp.json()
            if not data or not data.get("success"):
                continue
            markets = data.get("data") or []
            if isinstance(markets, list) and markets:
                return markets
        except Exception as e:
            logger.debug(f"fetch_token_markets error for {token_address} at {url}: {e}")
            continue
    return []


def _market_program_id(entry: Dict[str, Any]) -> Optional[str]:
    return (
        entry.get("programId")
        or entry.get("program_id")
        or entry.get("ammProgramId")
        or entry.get("marketProgramId")
        or entry.get("poolProgramId")
    )


def _get_num(entry: Dict[str, Any], keys: List[str]) -> float:
    for k in keys:
        if k in entry and entry[k] is not None:
            try:
                return float(entry[k])
            except Exception:
                continue
    return 0.0


def aggregate_filtered_market_metrics(
    markets: List[Dict[str, Any]],
    excluded_program_ids: List[str],
) -> Dict[str, float]:
    """
    Aggregate liquidity and time-window metrics across markets not in excluded list.
    Known keys vary by endpoint; we attempt common variants with graceful fallback.
    Returns a dict with keys: liquidity, trade_1h, volume_1h, trade_5m, volume_5m, volume_buy_5m, volume_sell_5m.
    """
    result = {
        "liquidity": 0.0,
        "trade_1h": 0.0,
        "volume_1h": 0.0,
        "trade_5m": 0.0,
        "volume_5m": 0.0,
        "volume_buy_5m": 0.0,
        "volume_sell_5m": 0.0,
    }

    for m in markets:
        pid = _market_program_id(m)
        if pid and pid in excluded_program_ids:
            continue

        result["liquidity"] += _get_num(m, ["liquidity"])  # pool liquidity

        # trades
        result["trade_1h"] += _get_num(m, ["trade_1h", "trades_1h", "t1h"])  # count
        result["trade_5m"] += _get_num(m, ["trade_5m", "trades_5m", "t5m"])  # count

        # volumes
        result["volume_1h"] += _get_num(m, ["volume_1h", "v1h", "vol_1h"])  # amount
        result["volume_5m"] += _get_num(m, ["volume_5m", "v5m", "vol_5m"])  # amount
        result["volume_buy_5m"] += _get_num(m, ["volume_buy_5m", "vBuy5m", "buy_vol_5m"])  # amount
        result["volume_sell_5m"] += _get_num(m, ["volume_sell_5m", "vSell5m", "sell_vol_5m"])  # amount

    return result

