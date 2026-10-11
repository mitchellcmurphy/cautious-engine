from datetime import date

from app.caching.memory import InMemoryTTLCache
from app.clients import yahoo_client
from app.clients.yahoo_client import TrailingReturns
from app.config import Settings
from app.schemas.filing import FilingMeta, FilingsSummaryResponse, FilingSummary
from app.schemas.portfolio import HoldingPosition
from app.schemas.recommendation import (
    NotOwnedRecommendationContent,
    OwnedRecommendationContent,
)
from app.services import filing_service, portfolio_service, recommendation_service


def _settings() -> Settings:
    return Settings(sec_contact_email="test@example.com", openai_api_key="sk-test")


def _fake_filings_response(ticker: str) -> FilingsSummaryResponse:
    meta = FilingMeta(
        form_type="10-Q",
        filing_date=date(2026, 7, 31),
        period_of_report=date(2026, 6, 27),
        accession_number="0000000000-26-000001",
        primary_document_url="https://www.sec.gov/Archives/edgar/data/1/1/doc.htm",
    )
    summary = FilingSummary(
        meta=meta,
        tldr="TLDR",
        overview="Overview",
        financial_highlights=[],
        notable_risks_or_changes=["Some risk"],
        sentiment="positive",
        confidence="high",
        generated_at="2026-10-11T00:00:00Z",
    )
    return FilingsSummaryResponse(
        ticker=ticker,
        company_name=f"{ticker} Inc.",
        cik="0000000001",
        filings=[summary],
    )


def _fake_position(ticker: str) -> HoldingPosition:
    return HoldingPosition(
        ticker=ticker,
        name=f"{ticker} Inc.",
        sector="Information Technology",
        total_shares=100.0,
        total_cost_basis=1000.0,
        avg_price_per_share=10.0,
        current_price=20.0,
        market_value=2000.0,
        unrealized_gain_loss=1000.0,
        unrealized_gain_loss_pct=100.0,
    )


class _FakeOpenAIClient:
    async def complete_structured(self, system_prompt, user_prompt, schema_model):
        if schema_model is OwnedRecommendationContent:
            return OwnedRecommendationContent(
                action="hold", rationale="r", confidence="high", key_factors=["f"]
            )
        return NotOwnedRecommendationContent(
            action="buy", rationale="r", confidence="high", key_factors=["f"]
        )


async def _fake_get_filings_summary(**kwargs) -> FilingsSummaryResponse:
    return _fake_filings_response(kwargs["ticker"])


async def _fake_get_trailing_returns(ticker: str) -> TrailingReturns:
    return TrailingReturns(
        return_1m=1.0,
        return_3m=2.0,
        return_6m=3.0,
        return_1y=4.0,
        as_of=date(2026, 10, 9),
    )


async def test_get_recommendation_owned_returns_sell_or_hold_action(monkeypatch):
    async def fake_get_position(ticker, cache, settings):
        return _fake_position(ticker)

    monkeypatch.setattr(portfolio_service, "get_position", fake_get_position)
    monkeypatch.setattr(
        filing_service, "get_filings_summary", _fake_get_filings_summary
    )
    monkeypatch.setattr(
        yahoo_client, "get_trailing_returns", _fake_get_trailing_returns
    )

    result = await recommendation_service.get_recommendation(
        ticker="AAPL",
        sec_client=object(),
        openai_client=_FakeOpenAIClient(),
        cache=InMemoryTTLCache(),
        settings=_settings(),
    )

    assert result.owned is True
    assert result.action in ("sell", "hold")
    assert result.position is not None


async def test_get_recommendation_not_owned_returns_buy_or_pass_action(monkeypatch):
    async def fake_get_position(ticker, cache, settings):
        return None

    monkeypatch.setattr(portfolio_service, "get_position", fake_get_position)
    monkeypatch.setattr(
        filing_service, "get_filings_summary", _fake_get_filings_summary
    )
    monkeypatch.setattr(
        yahoo_client, "get_trailing_returns", _fake_get_trailing_returns
    )

    result = await recommendation_service.get_recommendation(
        ticker="GOOGL",
        sec_client=object(),
        openai_client=_FakeOpenAIClient(),
        cache=InMemoryTTLCache(),
        settings=_settings(),
    )

    assert result.owned is False
    assert result.action in ("buy", "pass")
    assert result.position is None
