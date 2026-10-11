from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class QuoteResponse(BaseModel):
    ticker: str
    company_name: str | None
    price: float
    currency: str
    change: float
    change_percent: float
    previous_close: float
    market_state: str
    as_of: datetime
    source: Literal["yahoo_finance"]
