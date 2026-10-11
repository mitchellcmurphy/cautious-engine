import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime

import pandas as pd
import yfinance as yf
from dateutil.relativedelta import relativedelta

from app.core.exceptions import TickerNotFoundError


@dataclass
class RawQuote:
    ticker: str
    company_name: str | None
    price: float
    currency: str
    change: float
    change_percent: float
    previous_close: float
    market_state: str
    as_of: datetime


def _fetch_info(ticker: str) -> dict:
    return yf.Ticker(ticker).info


async def get_quote(ticker: str) -> RawQuote:
    info = await asyncio.to_thread(_fetch_info, ticker)

    price = info.get("regularMarketPrice")
    previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    currency = info.get("currency")

    if price is None or previous_close is None or currency is None:
        raise TickerNotFoundError(ticker)

    as_of_epoch = info.get("regularMarketTime")
    as_of = (
        datetime.fromtimestamp(as_of_epoch, tz=UTC)
        if as_of_epoch is not None
        else datetime.now(tz=UTC)
    )

    return RawQuote(
        ticker=ticker.upper(),
        company_name=info.get("longName") or info.get("shortName"),
        price=price,
        currency=currency,
        change=info.get("regularMarketChange", price - previous_close),
        change_percent=info.get(
            "regularMarketChangePercent",
            (price - previous_close) / previous_close * 100,
        ),
        previous_close=previous_close,
        market_state=info.get("marketState", "UNKNOWN"),
        as_of=as_of,
    )


@dataclass
class TrailingReturns:
    return_1m: float | None
    return_3m: float | None
    return_6m: float | None
    return_1y: float | None
    as_of: date


def _fetch_history(ticker: str) -> pd.DataFrame:
    # 2y of history gives margin so the 1y-ago lookup never falls exactly on
    # (or past) the start of the series.
    return yf.Ticker(ticker).history(period="2y")


async def get_trailing_returns(ticker: str) -> TrailingReturns:
    history = await asyncio.to_thread(_fetch_history, ticker)
    if history.empty:
        raise TickerNotFoundError(ticker)

    closes = history["Close"]
    latest_date = closes.index[-1]
    latest_close = closes.iloc[-1]

    def return_for(months: int) -> float | None:
        target_date = latest_date - relativedelta(months=months)
        if target_date < closes.index[0]:
            return None
        past_close = closes.asof(target_date)
        if pd.isna(past_close):
            return None
        return (latest_close - past_close) / past_close * 100

    return TrailingReturns(
        return_1m=return_for(1),
        return_3m=return_for(3),
        return_6m=return_for(6),
        return_1y=return_for(12),
        as_of=latest_date.date(),
    )
