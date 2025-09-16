import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

JUP_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
SOL_MINT = "So11111111111111111111111111111111111111112"


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

