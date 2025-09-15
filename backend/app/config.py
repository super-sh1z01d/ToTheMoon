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
