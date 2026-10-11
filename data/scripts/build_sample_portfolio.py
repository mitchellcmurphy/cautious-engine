"""Builds data/sample_portfolio.json from real historical closing prices.

Each lot is specified as a trade date + dollar amount; the script looks up the
split-adjusted close on that date (or the next trading day) and buys whole
shares. Prices are split-adjusted but NOT dividend-adjusted, so shares and cost
basis are expressed in today's share terms and can be compared to live quotes.

Run from the repo root with the backend venv:
  backend/.venv/bin/python data/scripts/build_sample_portfolio.py
"""

import json
import math
from datetime import date, timedelta
from pathlib import Path

import yfinance as yf

OUT_PATH = Path(__file__).resolve().parents[1] / "sample_portfolio.json"
AS_OF = date(2026, 10, 11)

# ticker, name, sector (GICS), asset_type, [(trade_date, dollar_amount), ...]
HOLDINGS = [
    ("AAPL", "Apple Inc.", "Information Technology", "common_stock",
     [("2019-03-15", 60_000), ("2023-08-01", 40_000)]),
    ("MSFT", "Microsoft Corporation", "Information Technology", "common_stock",
     [("2020-06-01", 90_000)]),
    ("NVDA", "NVIDIA Corporation", "Information Technology", "common_stock",
     [("2023-01-17", 50_000), ("2026-02-02", 30_000)]),
    ("JPM", "JPMorgan Chase & Co.", "Financials", "common_stock",
     [("2021-02-01", 80_000)]),
    ("BRK-B", "Berkshire Hathaway Inc. Class B", "Financials", "common_stock",
     [("2021-08-02", 75_000)]),
    ("JNJ", "Johnson & Johnson", "Health Care", "common_stock",
     [("2020-09-01", 70_000)]),
    ("PFE", "Pfizer Inc.", "Health Care", "common_stock",
     [("2021-12-17", 60_000)]),
    ("XOM", "Exxon Mobil Corporation", "Energy", "common_stock",
     [("2022-03-01", 65_000)]),
    ("PG", "The Procter & Gamble Company", "Consumer Staples", "common_stock",
     [("2019-11-01", 70_000)]),
    ("TSM", "Taiwan Semiconductor Manufacturing Co. Ltd. (ADR)", "Information Technology", "adr",
     [("2024-07-11", 60_000)]),
]


def close_on_or_after(ticker: str, trade_date: str) -> tuple[str, float]:
    start = date.fromisoformat(trade_date)
    hist = yf.Ticker(ticker).history(
        start=start.isoformat(), end=(start + timedelta(days=7)).isoformat(), auto_adjust=False
    )
    if hist.empty:
        raise RuntimeError(f"No price data for {ticker} near {trade_date}")
    row_date, row = next(hist.iterrows())
    return row_date.date().isoformat(), round(float(row["Close"]), 4)


def main() -> None:
    holdings = []
    total_cost = 0.0
    for ticker, name, sector, asset_type, lot_specs in HOLDINGS:
        lots = []
        for i, (trade_date, amount) in enumerate(lot_specs, start=1):
            actual_date, price = close_on_or_after(ticker, trade_date)
            shares = math.floor(amount / price)
            cost = round(shares * price, 2)
            total_cost += cost
            lots.append({
                "lot_id": f"{ticker}-{i}",
                "trade_date": actual_date,
                "shares": shares,
                "price_per_share": price,
                "cost_basis": cost,
                "holding_period": "long_term"
                if date.fromisoformat(actual_date) <= AS_OF - timedelta(days=365)
                else "short_term",
            })
        holdings.append({
            "ticker": ticker,
            "name": name,
            "asset_type": asset_type,
            "sector": sector,
            "lots": lots,
        })

    portfolio = {
        "schema_version": 1,
        "portfolio_id": "sample-001",
        "name": "Sample Growth & Income Portfolio",
        "as_of": AS_OF.isoformat(),
        "base_currency": "USD",
        "account_type": "taxable",
        "investor_profile": {
            "risk_tolerance": "moderate",
            "objective": "growth_and_income",
            "time_horizon_years": 10,
        },
        "cash": {"amount": 25_000.00, "currency": "USD"},
        "holdings": holdings,
        "conventions": {
            "price_source": "yfinance close on trade_date (next trading day if closed)",
            "split_adjusted": True,
            "dividend_adjusted": False,
            "note": "shares and price_per_share are in current (post-split) share terms; "
                    "current value is not stored — derive it from live quotes",
        },
    }
    OUT_PATH.write_text(json.dumps(portfolio, indent=2) + "\n")

    for h in holdings:
        for lot in h["lots"]:
            print(f"{lot['lot_id']:<8}{lot['trade_date']}  {lot['shares']:>6} sh @ "
                  f"{lot['price_per_share']:>9.2f}  = {lot['cost_basis']:>11,.2f}  {lot['holding_period']}")
    print(f"total cost basis {total_cost:,.2f} + cash 25,000.00 → {OUT_PATH}")


if __name__ == "__main__":
    main()
