"""Freezes SEC filings into eval fixtures.

For each (ticker, form) it picks the most recent filing *at build time*, then
pins it by accession number so later eval runs are reproducible. Reuses the
backend's own SEC client and HTML extraction so fixture text is exactly what the
summarizer would see in production.

Writes:
  evals/data/fixtures.jsonl  — summarizer inputs (meta + extracted text); read by the API in replay mode
  evals/data/labels.jsonl    — XBRL facts (auto) + empty checklists for hand labelling; read only by scorers

Run from the repo root with the backend venv:
  backend/.venv/bin/python evals/scripts/build_fixtures.py
"""

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
DATA_DIR = REPO_ROOT / "evals" / "data"
sys.path.insert(0, str(BACKEND_DIR))

import httpx  # noqa: E402

from app.clients.sec_client import SecClient, select_recent_filings  # noqa: E402
from app.config import Settings  # noqa: E402
from app.extraction.html_to_text import extract_text  # noqa: E402

CASES = [
    ("AAPL", "10-Q"),
    ("MSFT", "10-K"),
]

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# First concept found wins, so companies that tag revenue differently still resolve.
KEY_FACTS = {
    "Revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "Gross profit": ["GrossProfit"],
    "Operating income": ["OperatingIncomeLoss"],
    "Net income": ["NetIncomeLoss"],
    "Diluted EPS": ["EarningsPerShareDiluted"],
    "Cash and cash equivalents": ["CashAndCashEquivalentsAtCarryingValue"],
}


def _period_type(start: str | None, end: str) -> str:
    if start is None:
        return "instant"
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days
    if days < 100:
        return "Q"
    if days < 200:
        return "6M"
    if days < 290:
        return "9M"
    return "FY"


def extract_facts(companyfacts: dict, accession: str, period_end: str | None) -> list[dict]:
    """Facts reported in this filing, incl. prior-period comparatives (is_current=False)."""
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    facts = []
    for name, concepts in KEY_FACTS.items():
        for concept in concepts:
            if concept not in us_gaap:
                continue
            rows = [
                (unit, row)
                for unit, unit_rows in us_gaap[concept]["units"].items()
                for row in unit_rows
                if row["accn"] == accession
            ]
            if not rows:
                continue
            seen = set()
            for unit, row in rows:
                key = (row.get("start"), row["end"], row["val"])
                if key in seen:
                    continue
                seen.add(key)
                facts.append(
                    {
                        "name": name,
                        "concept": concept,
                        "value": row["val"],
                        "unit": unit,
                        "start": row.get("start"),
                        "end": row["end"],
                        "period_type": _period_type(row.get("start"), row["end"]),
                        "is_current": row["end"] == period_end,
                    }
                )
            break
    return facts


async def build_case(
    ticker: str, form: str, sec: SecClient, http: httpx.AsyncClient, cik_map: dict
) -> tuple[dict, dict]:
    entry = cik_map[ticker]
    cik = entry["cik"]
    submissions = await sec.fetch_submissions(cik)
    [meta] = select_recent_filings(
        submissions, cik=cik, forms=[form], limit=1, lookback_months=18
    )

    html = await sec.fetch_filing_document(str(meta.primary_document_url))
    text = extract_text(html)

    resp = await http.get(COMPANYFACTS_URL.format(cik=cik), timeout=30)
    resp.raise_for_status()
    period_end = meta.period_of_report.isoformat() if meta.period_of_report else None
    facts = extract_facts(resp.json(), meta.accession_number, period_end)

    case_id = f"{ticker.lower()}-{form.lower()}-{period_end}"
    fixture = {
        "id": case_id,
        "ticker": ticker,
        "company_name": entry["title"],
        "cik": cik,
        "meta": json.loads(meta.model_dump_json()),
        "text": text,
    }
    label = {
        "id": case_id,
        "facts": facts,
        "must_mention": [],
        "must_not_claim": [],
    }
    return fixture, label


async def main() -> None:
    settings = Settings(_env_file=BACKEND_DIR / ".env")
    headers = {"User-Agent": f"{settings.app_name} ({settings.sec_contact_email})"}
    async with httpx.AsyncClient(headers=headers) as http:
        sec = SecClient(http, requests_per_second=settings.sec_requests_per_second)
        cik_map = await sec.fetch_ticker_cik_map()
        results = [await build_case(t, f, sec, http, cik_map) for t, f in CASES]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "fixtures.jsonl", "w") as f:
        for fixture, _ in results:
            f.write(json.dumps(fixture) + "\n")
    with open(DATA_DIR / "labels.jsonl", "w") as f:
        for _, label in results:
            f.write(json.dumps(label) + "\n")

    for fixture, label in results:
        m = fixture["meta"]
        print(
            f"{fixture['id']}: {m['form_type']} filed {m['filing_date']} "
            f"accn {m['accession_number']} — {len(fixture['text']):,} chars, "
            f"{len(label['facts'])} XBRL facts"
        )


if __name__ == "__main__":
    asyncio.run(main())
