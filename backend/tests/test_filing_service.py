import json
from pathlib import Path

import pytest

from app.caching.memory import InMemoryTTLCache
from app.config import Settings
from app.core.exceptions import NoRecentFilingsError, TickerNotFoundError
from app.services import filing_service

FIXTURES = Path(__file__).parent / "fixtures"


def _settings() -> Settings:
    return Settings(sec_contact_email="test@example.com", openai_api_key="sk-test")


class _FakeSecClient:
    def __init__(self, cik_map: dict, submissions: dict) -> None:
        self._cik_map = cik_map
        self._submissions = submissions

    async def fetch_ticker_cik_map(self) -> dict:
        return self._cik_map

    async def fetch_submissions(self, cik: str) -> dict:
        return self._submissions


async def test_resolve_cik_found():
    cik_map = {"AAPL": {"cik": "0000320193", "title": "Apple Inc."}}
    sec_client = _FakeSecClient(cik_map=cik_map, submissions={})

    cik, title = await filing_service.resolve_cik(
        "aapl", sec_client, InMemoryTTLCache(), _settings()
    )

    assert cik == "0000320193"
    assert title == "Apple Inc."


async def test_resolve_cik_unknown_ticker_raises():
    sec_client = _FakeSecClient(cik_map={}, submissions={})

    with pytest.raises(TickerNotFoundError):
        await filing_service.resolve_cik(
            "ZZZZ", sec_client, InMemoryTTLCache(), _settings()
        )


async def test_get_recent_filings_returns_filtered_list():
    submissions = json.loads((FIXTURES / "submissions_sample.json").read_text())
    sec_client = _FakeSecClient(cik_map={}, submissions=submissions)

    filings = await filing_service.get_recent_filings(
        ticker="AAPL",
        cik="0000320193",
        sec_client=sec_client,
        cache=InMemoryTTLCache(),
        settings=_settings(),
        forms=["10-K", "10-Q"],
        limit=2,
        lookback_months=1200,
    )

    assert len(filings) == 2


async def test_get_recent_filings_raises_when_none_found():
    submissions = json.loads((FIXTURES / "submissions_sample.json").read_text())
    sec_client = _FakeSecClient(cik_map={}, submissions=submissions)

    with pytest.raises(NoRecentFilingsError):
        await filing_service.get_recent_filings(
            ticker="AAPL",
            cik="0000320193",
            sec_client=sec_client,
            cache=InMemoryTTLCache(),
            settings=_settings(),
            forms=["8-K"],
            limit=2,
            lookback_months=1200,
        )
