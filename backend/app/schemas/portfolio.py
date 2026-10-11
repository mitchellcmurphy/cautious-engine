from datetime import date

from pydantic import BaseModel


class HoldingPosition(BaseModel):
    ticker: str
    name: str
    sector: str
    total_shares: float
    total_cost_basis: float
    avg_price_per_share: float
    current_price: float
    market_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_pct: float


class PortfolioResponse(BaseModel):
    portfolio_id: str
    name: str
    as_of: date
    cash: float
    holdings: list[HoldingPosition]
    total_market_value: float
    total_cost_basis: float
    total_unrealized_gain_loss: float
