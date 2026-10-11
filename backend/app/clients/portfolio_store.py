import json
from pathlib import Path


def load_portfolio(path: Path) -> dict:
    return json.loads(path.read_text())


def get_holding_tickers(raw_portfolio: dict) -> set[str]:
    return {holding["ticker"].upper() for holding in raw_portfolio["holdings"]}


def find_holding(raw_portfolio: dict, ticker: str) -> dict | None:
    ticker = ticker.upper()
    for holding in raw_portfolio["holdings"]:
        if holding["ticker"].upper() == ticker:
            return holding
    return None


def aggregate_lots(holding: dict) -> tuple[float, float, float]:
    """Returns (total_shares, total_cost_basis, avg_price_per_share) across a holding's lots."""
    total_shares = sum(lot["shares"] for lot in holding["lots"])
    total_cost_basis = sum(lot["cost_basis"] for lot in holding["lots"])
    avg_price_per_share = total_cost_basis / total_shares if total_shares else 0.0
    return total_shares, total_cost_basis, avg_price_per_share
