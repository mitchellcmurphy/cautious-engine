from datetime import date

import pandas as pd
import pytest

from app.clients import yahoo_client
from app.core.exceptions import TickerNotFoundError


def _synthetic_history() -> pd.DataFrame:
    # Daily business-day closes over ~15 months, rising linearly from 100 to 250,
    # so returns over each window are easy to sanity-check by hand.
    dates = pd.bdate_range(end="2026-10-09", periods=320, tz="America/New_York")
    closes = [100 + i * 0.5 for i in range(len(dates))]
    return pd.DataFrame({"Close": closes}, index=dates)


async def test_get_trailing_returns_computes_all_windows(monkeypatch):
    monkeypatch.setattr(
        yahoo_client, "_fetch_history", lambda ticker: _synthetic_history()
    )

    result = await yahoo_client.get_trailing_returns("FAKE")

    assert result.as_of == date(2026, 10, 9)
    assert result.return_1m is not None
    assert result.return_3m is not None
    assert result.return_6m is not None
    # linearly increasing series: longer windows should show larger cumulative return
    assert result.return_1m < result.return_3m < result.return_6m


async def test_get_trailing_returns_window_beyond_history_is_none(monkeypatch):
    short_history = _synthetic_history().iloc[-10:]  # only ~2 weeks of data
    monkeypatch.setattr(yahoo_client, "_fetch_history", lambda ticker: short_history)

    result = await yahoo_client.get_trailing_returns("FAKE")

    assert result.return_1m is None
    assert result.return_3m is None
    assert result.return_6m is None
    assert result.return_1y is None


async def test_get_trailing_returns_empty_history_raises_ticker_not_found(monkeypatch):
    monkeypatch.setattr(
        yahoo_client, "_fetch_history", lambda ticker: pd.DataFrame({"Close": []})
    )

    with pytest.raises(TickerNotFoundError):
        await yahoo_client.get_trailing_returns("NOTREAL")
