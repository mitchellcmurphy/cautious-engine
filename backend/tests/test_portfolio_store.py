from pathlib import Path

import pytest

from app.clients import portfolio_store

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_portfolio.json"


@pytest.fixture
def raw_portfolio():
    return portfolio_store.load_portfolio(DATA_PATH)


def test_load_portfolio_parses_real_fixture(raw_portfolio):
    assert raw_portfolio["portfolio_id"] == "sample-001"
    assert len(raw_portfolio["holdings"]) > 0


def test_get_holding_tickers_includes_known_holdings(raw_portfolio):
    tickers = portfolio_store.get_holding_tickers(raw_portfolio)
    assert "AAPL" in tickers
    assert "MSFT" in tickers
    assert "GOOGL" not in tickers


def test_find_holding_is_case_insensitive(raw_portfolio):
    holding = portfolio_store.find_holding(raw_portfolio, "aapl")
    assert holding is not None
    assert holding["ticker"] == "AAPL"


def test_find_holding_returns_none_when_absent(raw_portfolio):
    assert portfolio_store.find_holding(raw_portfolio, "GOOGL") is None


def test_aggregate_lots_sums_multiple_lots(raw_portfolio):
    aapl = portfolio_store.find_holding(raw_portfolio, "AAPL")
    total_shares, total_cost_basis, avg_price = portfolio_store.aggregate_lots(aapl)

    assert total_shares == 1289 + 204
    assert total_cost_basis == pytest.approx(59977.17 + 39904.44)
    assert avg_price == pytest.approx(total_cost_basis / total_shares)


def test_aggregate_lots_single_lot(raw_portfolio):
    msft = portfolio_store.find_holding(raw_portfolio, "MSFT")
    total_shares, total_cost_basis, avg_price = portfolio_store.aggregate_lots(msft)

    assert total_shares == 492
    assert total_cost_basis == pytest.approx(89952.36)
    assert avg_price == pytest.approx(182.83, rel=1e-3)
