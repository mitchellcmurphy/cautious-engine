import json
from datetime import date, timedelta
from pathlib import Path

import httpx
import pytest
import respx

from app.clients.sec_client import (
    SUBMISSIONS_URL,
    TICKERS_URL,
    SecClient,
    select_recent_filings,
)
from app.core.exceptions import UpstreamServiceError

FIXTURES = Path(__file__).parent / "fixtures"


def _client() -> SecClient:
    http_client = httpx.AsyncClient(headers={"User-Agent": "test (test@example.com)"})
    return SecClient(http_client=http_client, requests_per_second=100)


@respx.mock
async def test_fetch_ticker_cik_map_parses_and_zero_pads():
    fixture = json.loads((FIXTURES / "company_tickers_sample.json").read_text())
    respx.get(TICKERS_URL).mock(return_value=httpx.Response(200, json=fixture))

    result = await _client().fetch_ticker_cik_map()

    assert result["AAPL"] == {"cik": "0000320193", "title": "Apple Inc."}
    assert result["NVDA"]["cik"] == "0001045810"


@respx.mock
async def test_fetch_ticker_cik_map_upstream_failure_raises():
    respx.get(TICKERS_URL).mock(return_value=httpx.Response(500))

    with pytest.raises(UpstreamServiceError):
        await _client().fetch_ticker_cik_map()


@respx.mock
async def test_fetch_submissions_parses_response():
    fixture = json.loads((FIXTURES / "submissions_sample.json").read_text())
    url = SUBMISSIONS_URL.format(cik="0000320193")
    respx.get(url).mock(return_value=httpx.Response(200, json=fixture))

    result = await _client().fetch_submissions("0000320193")

    assert result["cik"] == "320193"


def test_select_recent_filings_sorts_desc_and_respects_limit():
    fixture = json.loads((FIXTURES / "submissions_sample.json").read_text())

    filings = select_recent_filings(
        submissions=fixture,
        cik="320193",
        forms=["10-K", "10-Q"],
        limit=2,
        lookback_months=1200,  # effectively unbounded, avoids date.today() flakiness
    )

    assert len(filings) == 2
    assert filings[0].filing_date == date(2026, 7, 31)
    assert filings[1].filing_date == date(2026, 5, 1)
    assert filings[0].accession_number == "0000320193-26-000020"
    assert str(filings[0].primary_document_url) == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019326000020/aapl-20260627.htm"
    )


def test_select_recent_filings_filters_by_form_type():
    fixture = json.loads((FIXTURES / "submissions_sample.json").read_text())

    filings = select_recent_filings(
        submissions=fixture,
        cik="320193",
        forms=["10-K"],
        limit=5,
        lookback_months=1200,
    )

    assert len(filings) == 1
    assert filings[0].form_type == "10-K"


def test_select_recent_filings_respects_lookback_window():
    today = date.today()
    recent = {
        "accessionNumber": ["0000000000-26-000001", "0000000000-26-000002"],
        "filingDate": [
            (today - timedelta(days=10)).isoformat(),
            (today - timedelta(days=900)).isoformat(),
        ],
        "reportDate": [None, None],
        "form": ["10-Q", "10-Q"],
        "primaryDocument": ["recent.htm", "old.htm"],
    }
    submissions = {"filings": {"recent": recent}}

    filings = select_recent_filings(
        submissions=submissions,
        cik="1",
        forms=["10-Q"],
        limit=5,
        lookback_months=18,
    )

    assert len(filings) == 1
    assert filings[0].accession_number == "0000000000-26-000001"


def test_select_recent_filings_empty_when_no_match():
    fixture = json.loads((FIXTURES / "submissions_sample.json").read_text())

    filings = select_recent_filings(
        submissions=fixture,
        cik="320193",
        forms=["8-K"],
        limit=5,
        lookback_months=1200,
    )

    assert filings == []
