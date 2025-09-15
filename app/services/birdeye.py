from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import aiohttp

from app.core.config import settings
from app.services.cache import TTLCache

logger = logging.getLogger("app.services.birdeye")


_cache = TTLCache()
_sem = asyncio.Semaphore(settings.EXT_MAX_CONCURRENCY)
_session: aiohttp.ClientSession | None = None


def _cache_key(path: str, params: Optional[dict]) -> str:
    return f"{path}?{json.dumps(params or {}, sort_keys=True)}"


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def close_session() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()


async def fetch_json(
    path: str,
    params: Optional[dict] = None,
    *,
    use_cache: bool = True,
    ttl: Optional[int] = None,
) -> Dict[str, Any]:
    base = settings.BIRDEYE_BASE_URL.rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    headers = {}
    if settings.BIRDEYE_API_KEY:
        headers["x-api-key"] = settings.BIRDEYE_API_KEY

    ckey = _cache_key(path, params)
    if use_cache:
        cached = _cache.get(ckey)
        if cached is not None:
            return cached

    async with _sem:
        session = await _get_session()
        backoff = 1.0
        for attempt in range(1, 4):
            try:
                async with session.get(url, params=params, headers=headers, timeout=20) as resp:
                    if resp.status >= 500 or resp.status == 429:
                        raise aiohttp.ClientResponseError(
                            resp.request_info, resp.history, status=resp.status
                        )
                    resp.raise_for_status()
                    data = await resp.json()
                    if use_cache:
                        _cache.set(ckey, data, ttl or settings.BIRDEYE_CACHE_TTL)
                    return data
            except (aiohttp.ClientResponseError, aiohttp.ClientConnectorError) as e:
                if attempt == 3:
                    logger.error("birdeye.request_failed", extra={"url": url, "status": getattr(e, "status", None)})
                    raise
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 8)


# Example high-level helper (expand as needed)
async def token_overview(mint: str) -> Dict[str, Any]:
    return await fetch_json("defi/token_overview", params={"address": mint}, use_cache=True)

