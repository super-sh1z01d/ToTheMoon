import logging
import time
from typing import Any, Dict, List, Tuple

import httpx

logger = logging.getLogger(__name__)

JUP_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G2P8oHGt61i"

# Simple in-memory cache for programs per token
_PROGRAMS_CACHE: Dict[str, Tuple[float, List[str]]] = {}
# TTL (seconds) will be injected from config at import time in main app; default 600s
from ...config import JUPITER_PROGRAMS_CACHE_TTL_SECONDS  # type: ignore


async def has_allowed_route(
    token_mint: str,
    allowed_programs: List[str],
    amount: int = 100000,  # small amount in minor units
) -> bool:
    """
    Checks if there is any direct route through allowed program IDs.
    Returns True if at least one route uses allowed program.
    """
    params = {
        "inputMint": token_mint,
        "outputMint": SOL_MINT,
        "amount": str(amount),
        "slippageBps": "50",
        "onlyDirectRoutes": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(JUP_QUOTE_URL, params=params)
            if r.status_code != 200:
                return False
            data = r.json() or {}
            routes = data.get("data") or []
            al = set(a.lower() for a in allowed_programs)
            for route in routes:
                for rp in route.get("routePlan", []):
                    mi = rp.get("marketInfos") or rp.get("marketInfo") or {}
                    # marketInfos can be a list or single dict depending on version
                    if isinstance(mi, list):
                        infos = mi
                    else:
                        infos = [mi]
                    for info in infos:
                        pid = (info.get("programId") or "").lower()
                        if pid in al:
                            return True
            return False
    except Exception as e:
        logger.debug(f"Jupiter quote error for {token_mint}: {e}")
        return False


async def list_programs_for_token(token_mint: str, amount: int = 100000) -> List[str]:
    """
    Returns a list of programIds observed in direct routes for given token
    against SOL and USDC. Best-effort; may return empty on no routes.
    """
    # Cache check
    now = time.time()
    item = _PROGRAMS_CACHE.get(token_mint)
    if item:
        ts, programs_cached = item
        if now - ts < PROGRAMS_CACHE_TTL_SECONDS:
            return programs_cached

    programs: set[str] = set()
    async with httpx.AsyncClient(timeout=5.0) as client:
        for out_mint in (SOL_MINT, USDC_MINT):
            params = {
                "inputMint": token_mint,
                "outputMint": out_mint,
                "amount": str(amount),
                "slippageBps": "50",
                "onlyDirectRoutes": "true",
            }
            try:
                r = await client.get(JUP_QUOTE_URL, params=params)
                if r.status_code != 200:
                    continue
                data = r.json() or {}
                routes = data.get("data") or []
                for route in routes:
                    for rp in route.get("routePlan", []):
                        mi = rp.get("marketInfos") or rp.get("marketInfo") or {}
                        infos = mi if isinstance(mi, list) else [mi]
                        for info in infos:
                            pid = info.get("programId")
                            if pid:
                                programs.add(pid)
            except Exception as e:
                logger.debug(f"Jupiter quote list_programs error for {token_mint}: {e}")
                continue
    programs_list = list(programs)
    _PROGRAMS_CACHE[token_mint] = (now, programs_list)
    return programs_list
