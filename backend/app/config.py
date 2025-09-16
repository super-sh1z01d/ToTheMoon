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
