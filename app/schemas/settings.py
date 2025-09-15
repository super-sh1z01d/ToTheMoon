from __future__ import annotations

from pydantic import BaseModel, Field, confloat


class WeightsModel(BaseModel):
    Tx_Accel: confloat(ge=0) = Field(0.25)
    Vol_Momentum: confloat(ge=0) = Field(0.25)
    Holder_Growth: confloat(ge=0) = Field(0.25)
    Orderflow_Imbalance: confloat(ge=0) = Field(0.25)


class ScoringSettings(BaseModel):
    weights: WeightsModel = Field(default_factory=WeightsModel)
    ewma_alpha: confloat(ge=0, le=1) = Field(0.5)
    min_active_liquidity: confloat(ge=0) = Field(1000.0)
    min_score_keep_active: confloat(ge=0) = Field(0.1)
    degrade_checks: int = Field(10, ge=1)
    degrade_window_hours: int = Field(6, ge=1)
    min_tx_count: int = Field(300, ge=0)
