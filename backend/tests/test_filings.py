import json
from pathlib import Path

from app.core.exceptions import SummarizationError
from app.deps import get_openai_client, get_sec_client
from app.main import app
from app.schemas.filing import GeneratedSummaryContent

FIXTURES = Path(__file__).parent / "fixtures"

SAMPLE_SUMMARY = GeneratedSummaryContent(
    tldr="TLDR",
    overview="Overview",
    financial_highlights=[],
    notable_risks_or_changes=[],
    sentiment="neutral",
    confidence="high",
)


class _FakeSecClient:
    def __init__(
        self, cik_map=None, submissions=None, document_text="<html>filing text</html>"
    ):
        self._cik_map = cik_map or {}
        self._submissions = submissions or {}
        self._document_text = document_text

    async def fetch_ticker_cik_map(self):
        return self._cik_map

    async def fetch_submissions(self, cik: str):
        return self._submissions

    async def fetch_filing_document(self, url: str):
        return self._document_text


class _FakeOpenAIClient:
    def __init__(self, fail: bool = False):
        self._fail = fail

    async def complete_text(self, system_prompt, user_prompt):
        return "notes"

    async def complete_structured(self, system_prompt, user_prompt, schema_model):
        if self._fail:
            raise SummarizationError("mock failure")
        return SAMPLE_SUMMARY


def _cik_map_and_submissions():
    cik_map = {"AAPL": {"cik": "0000320193", "title": "Apple Inc."}}
    submissions = json.loads((FIXTURES / "submissions_sample.json").read_text())
    return cik_map, submissions


def test_read_filings_summary_success(client):
    cik_map, submissions = _cik_map_and_submissions()
    app.dependency_overrides[get_sec_client] = lambda: _FakeSecClient(
        cik_map, submissions
    )
    app.dependency_overrides[get_openai_client] = lambda: _FakeOpenAIClient()

    response = client.get("/filings/AAPL/summary?limit=2&lookback_months=60")

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["cik"] == "0000320193"
    assert len(body["filings"]) == 2
    assert body["warnings"] == []


def test_read_filings_summary_unknown_ticker_returns_404(client):
    app.dependency_overrides[get_sec_client] = lambda: _FakeSecClient({}, {})
    app.dependency_overrides[get_openai_client] = lambda: _FakeOpenAIClient()

    response = client.get("/filings/NOTREAL123/summary")

    assert response.status_code == 404
    assert response.json()["error"] == "ticker_not_found"


def test_read_filings_summary_all_summarization_failures_returns_502(client):
    cik_map, submissions = _cik_map_and_submissions()
    app.dependency_overrides[get_sec_client] = lambda: _FakeSecClient(
        cik_map, submissions
    )
    app.dependency_overrides[get_openai_client] = lambda: _FakeOpenAIClient(fail=True)

    response = client.get("/filings/AAPL/summary?limit=2&lookback_months=60")

    assert response.status_code == 502
    assert response.json()["error"] == "summarization_failed"
