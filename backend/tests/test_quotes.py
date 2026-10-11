from datetime import UTC, datetime

from app.clients import yahoo_client
from app.clients.yahoo_client import RawQuote
from app.core.exceptions import TickerNotFoundError


def test_read_quote_success(client, monkeypatch):
    async def fake_get_quote(ticker: str) -> RawQuote:
        return RawQuote(
            ticker="AAPL",
            company_name="Apple Inc.",
            price=336.64,
            currency="USD",
            change=-3.78,
            change_percent=-1.11,
            previous_close=340.42,
            market_state="CLOSED",
            as_of=datetime.now(tz=UTC),
        )

    monkeypatch.setattr(yahoo_client, "get_quote", fake_get_quote)

    response = client.get("/quotes/AAPL")

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["price"] == 336.64
    assert body["source"] == "yahoo_finance"


def test_read_quote_unknown_ticker_returns_404(client, monkeypatch):
    async def fake_get_quote(ticker: str) -> RawQuote:
        raise TickerNotFoundError(ticker)

    monkeypatch.setattr(yahoo_client, "get_quote", fake_get_quote)

    response = client.get("/quotes/NOTREAL123")

    assert response.status_code == 404
    assert response.json()["error"] == "ticker_not_found"
