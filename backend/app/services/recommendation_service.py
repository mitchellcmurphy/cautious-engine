from datetime import UTC, datetime

from app.caching.base import Cache
from app.clients import yahoo_client
from app.clients.openai_client import OpenAIClient
from app.clients.sec_client import SecClient
from app.clients.yahoo_client import TrailingReturns
from app.config import Settings
from app.schemas.filing import FilingSummary
from app.schemas.portfolio import HoldingPosition
from app.schemas.recommendation import (
    NotOwnedRecommendationContent,
    OwnedRecommendationContent,
    PerformanceSnapshot,
    RecommendationResponse,
)
from app.services import filing_service, portfolio_service

SYSTEM_PROMPT = (
    "You are an investment analyst assistant advising a wealth management team. "
    "Base your recommendation only on the filing summaries and performance data "
    "provided below — do not speculate beyond them. Be direct and specific in "
    "key_factors, citing concrete figures or statements from the input."
)

OWNED_PROMPT_TEMPLATE = """\
The firm currently holds {ticker} ({company_name}). Decide whether to SELL or HOLD.

POSITION:
- Shares: {shares}
- Average cost per share: ${avg_cost:.2f}
- Current price: ${current_price:.2f}
- Unrealized gain/loss: ${gain_loss:,.2f} ({gain_loss_pct:+.1f}%)

TRAILING PRICE RETURNS (as of {perf_as_of}):
{performance_block}

RECENT FILING SUMMARIES:
{filings_block}
"""

NOT_OWNED_PROMPT_TEMPLATE = """\
The firm does not currently hold {ticker} ({company_name}). Decide whether to BUY or PASS.

TRAILING PRICE RETURNS (as of {perf_as_of}):
{performance_block}

RECENT FILING SUMMARIES:
{filings_block}
"""


def _format_performance(performance: TrailingReturns) -> str:
    def fmt(value: float | None) -> str:
        return f"{value:+.1f}%" if value is not None else "unknown"

    return (
        f"- 1 month: {fmt(performance.return_1m)}\n"
        f"- 3 month: {fmt(performance.return_3m)}\n"
        f"- 6 month: {fmt(performance.return_6m)}\n"
        f"- 1 year: {fmt(performance.return_1y)}"
    )


def _format_filings(filings: list[FilingSummary]) -> str:
    blocks = []
    for f in filings:
        highlights = "; ".join(f"{h.label}: {h.value}" for h in f.financial_highlights)
        risks = "; ".join(f.notable_risks_or_changes)
        blocks.append(
            f"[{f.meta.form_type} filed {f.meta.filing_date}] {f.tldr}\n"
            f"  Overview: {f.overview}\n"
            f"  Financial highlights: {highlights or 'none reported'}\n"
            f"  Notable risks/changes: {risks or 'none reported'}\n"
            f"  Sentiment: {f.sentiment}"
        )
    return "\n\n".join(blocks)


async def get_recommendation(
    ticker: str,
    sec_client: SecClient,
    openai_client: OpenAIClient,
    cache: Cache,
    settings: Settings,
) -> RecommendationResponse:
    ticker = ticker.upper()

    position = await portfolio_service.get_position(ticker, cache, settings)
    owned = position is not None

    filings_response = await filing_service.get_filings_summary(
        ticker=ticker,
        sec_client=sec_client,
        openai_client=openai_client,
        cache=cache,
        settings=settings,
        forms=["10-K", "10-Q"],
        limit=2,
        lookback_months=18,
    )

    performance = await cache.get_or_set(
        key=f"performance:{ticker}",
        factory=lambda: yahoo_client.get_trailing_returns(ticker),
        ttl_seconds=settings.performance_cache_ttl_seconds,
    )

    async def factory() -> RecommendationResponse:
        generated = await _generate_recommendation(
            ticker=ticker,
            company_name=filings_response.company_name,
            owned=owned,
            position=position,
            performance=performance,
            filings=filings_response.filings,
            openai_client=openai_client,
        )
        return RecommendationResponse(
            ticker=ticker,
            company_name=filings_response.company_name,
            owned=owned,
            action=generated.action,
            rationale=generated.rationale,
            confidence=generated.confidence,
            key_factors=generated.key_factors,
            performance=PerformanceSnapshot(
                return_1m=performance.return_1m,
                return_3m=performance.return_3m,
                return_6m=performance.return_6m,
                return_1y=performance.return_1y,
                as_of=performance.as_of,
            ),
            position=position,
            based_on_filings=[f.meta for f in filings_response.filings],
            generated_at=datetime.now(tz=UTC),
        )

    return await cache.get_or_set(
        key=f"recommendation:{ticker}:{owned}",
        factory=factory,
        ttl_seconds=settings.recommendation_cache_ttl_seconds,
    )


async def _generate_recommendation(
    ticker: str,
    company_name: str | None,
    owned: bool,
    position: HoldingPosition | None,
    performance: TrailingReturns,
    filings: list[FilingSummary],
    openai_client: OpenAIClient,
) -> OwnedRecommendationContent | NotOwnedRecommendationContent:
    performance_block = _format_performance(performance)
    filings_block = _format_filings(filings)

    if owned:
        assert position is not None
        prompt = OWNED_PROMPT_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name or ticker,
            shares=position.total_shares,
            avg_cost=position.avg_price_per_share,
            current_price=position.current_price,
            gain_loss=position.unrealized_gain_loss,
            gain_loss_pct=position.unrealized_gain_loss_pct,
            perf_as_of=performance.as_of,
            performance_block=performance_block,
            filings_block=filings_block,
        )
        return await openai_client.complete_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            schema_model=OwnedRecommendationContent,
        )

    prompt = NOT_OWNED_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name or ticker,
        perf_as_of=performance.as_of,
        performance_block=performance_block,
        filings_block=filings_block,
    )
    return await openai_client.complete_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        schema_model=NotOwnedRecommendationContent,
    )
