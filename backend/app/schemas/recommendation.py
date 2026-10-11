from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.filing import FilingMeta
from app.schemas.portfolio import HoldingPosition


class PerformanceSnapshot(BaseModel):
    return_1m: float | None
    return_3m: float | None
    return_6m: float | None
    return_1y: float | None
    as_of: date


class OwnedRecommendationContent(BaseModel):
    """LLM-facing schema when the firm already holds the position."""

    action: Literal["sell", "hold"]
    rationale: str
    confidence: Literal["high", "medium", "low"]
    key_factors: list[str]


class NotOwnedRecommendationContent(BaseModel):
    """LLM-facing schema when the firm does not hold the position."""

    action: Literal["buy", "pass"]
    rationale: str
    confidence: Literal["high", "medium", "low"]
    key_factors: list[str]


class RecommendationResponse(BaseModel):
    ticker: str
    company_name: str | None
    owned: bool
    action: Literal["buy", "sell", "hold", "pass"]
    rationale: str
    confidence: Literal["high", "medium", "low"]
    key_factors: list[str]
    performance: PerformanceSnapshot
    position: HoldingPosition | None
    based_on_filings: list[FilingMeta]
    generated_at: datetime
