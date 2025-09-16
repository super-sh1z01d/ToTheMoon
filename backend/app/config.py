import os
import json
from typing import Dict

DEFAULT_WEIGHTS: Dict[str, float] = {
    "W_tx": 0.25,
    "W_vol": 0.25,
    "W_hld": 0.25,
    "W_oi": 0.25,
    "EWMA_ALPHA": 0.3, # Smoothing factor
    "POLLING_INTERVAL_INITIAL": 60, # seconds
    "POLLING_INTERVAL_ACTIVE": 300, # seconds
    "POLLING_INTERVAL_ARCHIVED": 0, # seconds (0 means disabled)
    "MIN_SCORE_THRESHOLD": 0.05, # Minimum score to remain Active
    "MIN_SCORE_DURATION_HOURS": 6, # Hours score can be below threshold before status change
    "MIN_LIQUIDITY_USD": 500, # Minimum liquidity in USD for activation
    "MIN_TX_COUNT": 300, # Minimum total transaction count for activation
}

# Program IDs whose pools should be ignored (e.g., Bonding Curve)
EXCLUDED_POOL_PROGRAMS = [
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
]

# DexScreener DEX IDs to exclude (Bonding Curve)
EXCLUDED_DEX_IDS = [
    "pumpfun",
]

# Allowed program IDs (DEX) for verification via Jupiter
ALLOWED_POOL_PROGRAMS = [
    # Raydium
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # AMM
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",  # CPMM
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",  # CLMM
    # Meteora
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",  # DLMM
    "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",  # DAMMV2
    # Orca Whirlpool
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
    # GOOSEFX (GAMMA)
    "GAMMA7meSFWaBXF25oSUgmGRwaW6sCMFLmBNiMSdbHVT",
]

# Mapping of DexScreener dexId -> list of Solana program IDs (used for Jupiter cross-check)
DEX_PROGRAM_MAP: Dict[str, list] = {
    # Raydium
    "raydium": [
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # AMM
        "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",  # CPMM
        "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",  # CLMM
    ],
    # Meteora
    "meteora": [
        "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",  # DLMM
        "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",  # DAMMV2
    ],
    # Orca Whirlpool
    "whirlpool": [
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
    ],
    "orca": [
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
    ],
    # GOOSEFX (GAMMA)
    "goosefx": [
        "GAMMA7meSFWaBXF25oSUgmGRwaW6sCMFLmBNiMSdbHVT",
    ],
    "gamma": [
        "GAMMA7meSFWaBXF25oSUgmGRwaW6sCMFLmBNiMSdbHVT",
    ],
}

# Optional: extend allowed programs and dex map via environment variables
# ALLOWED_POOL_PROGRAMS_EXTRA='["<programId>", ...]'
try:
    _allowed_extra = os.getenv("ALLOWED_POOL_PROGRAMS_EXTRA")
    if _allowed_extra:
        _lst = json.loads(_allowed_extra)
        if isinstance(_lst, list):
            for pid in _lst:
                pid = str(pid)
                if pid not in ALLOWED_POOL_PROGRAMS:
                    ALLOWED_POOL_PROGRAMS.append(pid)
except Exception:
    pass

# DEX_PROGRAM_MAP_EXTRA='{"dexid":["programId1","programId2"], ...}'
try:
    _dexmap_extra = os.getenv("DEX_PROGRAM_MAP_EXTRA")
    if _dexmap_extra:
        _mp = json.loads(_dexmap_extra)
        if isinstance(_mp, dict):
            for dexid, progs in _mp.items():
                if not isinstance(progs, list):
                    continue
                dexid = str(dexid)
                DEX_PROGRAM_MAP.setdefault(dexid, [])
                for pid in progs:
                    pid = str(pid)
                    if pid not in DEX_PROGRAM_MAP[dexid]:
                        DEX_PROGRAM_MAP[dexid].append(pid)
except Exception:
    pass

# TTL for caching Jupiter programs per token (seconds)
JUPITER_PROGRAMS_CACHE_TTL_SECONDS = int(os.getenv("JUPITER_PROGRAMS_CACHE_TTL_SECONDS", "600"))

# TTL for DexScreener token pairs cache (seconds)
DEXSCREENER_CACHE_TTL_SECONDS = int(os.getenv("DEXSCREENER_CACHE_TTL_SECONDS", "30"))
