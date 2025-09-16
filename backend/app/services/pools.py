import logging
from typing import Any, Dict, List

from sqlmodel import select
from sqlmodel import Session

from ..models.models import Pool
from ..config import DEX_PROGRAM_MAP, ALLOWED_POOL_PROGRAMS
from .markets.dexscreener import fetch_pairs as ds_fetch_pairs

logger = logging.getLogger(__name__)


def _filter_pairs_by_program(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    allowed = {p.lower() for p in ALLOWED_POOL_PROGRAMS}
    kept: List[Dict[str, Any]] = []
    for p in pairs:
        dex_id = (p.get("dexId") or "").lower()
        prog_ids = [pid.lower() for pid in DEX_PROGRAM_MAP.get(dex_id, [])]
        if any(pid in allowed for pid in prog_ids):
            kept.append(p)
    return kept


async def update_token_pools(session: Session, token_id: int, token_address: str) -> int:
    """Fetch pools via DexScreener and whitelist by local config; persist to DB.

    Returns number of pools ensured (inserted or already existing) for the token.
    """
    try:
        ds = await ds_fetch_pairs(token_address)
    except Exception as e:
        logger.debug(f"DexScreener fetch error for pools {token_address}: {e}")
        return 0

    pairs = ds.get("pairs") or []
    if not isinstance(pairs, list) or not pairs:
        return 0

    allowed_pairs = _filter_pairs_by_program(pairs)
    count = 0
    for p in allowed_pairs:
        pool_addr = p.get("pairAddress") or p.get("address")
        dex_name = p.get("dexId") or ""
        if not pool_addr:
            continue
        existing = session.exec(select(Pool).where(Pool.pool_address == pool_addr)).first()
        if existing:
            # Ensure linkage and name
            changed = False
            if existing.token_id != token_id:
                existing.token_id = token_id
                changed = True
            if dex_name and existing.dex_name != dex_name:
                existing.dex_name = dex_name
                changed = True
            if changed:
                session.add(existing)
        else:
            session.add(Pool(pool_address=pool_addr, dex_name=dex_name, token_id=token_id))
        count += 1
    return count

