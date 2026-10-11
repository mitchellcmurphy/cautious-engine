from datetime import UTC, datetime

from app.clients import yahoo_client
from app.clients.yahoo_client import RawQuote


def _fake_quote_factory():
    async def fake_get_quote(ticker: str) -> RawQuote:
        return RawQuote(
            ticker=ticker.upper(),
            company_name=f"{ticker} Inc.",
            price=100.0,
            currency="USD",
            change=1.0,
            change_percent=1.0,
            previous_close=99.0,
            market_state="CLOSED",
            as_of=datetime.now(tz=UTC),
        )

    return fake_get_quote


def test_read_portfolio_returns_all_holdings_with_live_prices(client, monkeypatch):
    monkeypatch.setattr(yahoo_client, "get_quote", _fake_quote_factory())

    response = client.get("/portfolio")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "sample-001"
    assert len(body["holdings"]) == 10
    for holding in body["holdings"]:
        assert holding["current_price"] == 100.0
        assert holding["market_value"] == holding["total_shares"] * 100.0

    expected_total = sum(h["market_value"] for h in body["holdings"]) + body["cash"]
    assert body["total_market_value"] == expected_total
