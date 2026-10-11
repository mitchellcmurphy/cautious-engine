import logging
from datetime import UTC, datetime

from app.caching.base import Cache
from app.clients.openai_client import OpenAIClient
from app.clients.sec_client import SecClient, select_recent_filings
from app.config import Settings
from app.core.exceptions import (
    NoRecentFilingsError,
    SummarizationError,
    TickerNotFoundError,
)
from app.extraction.html_to_text import extract_text
from app.schemas.filing import FilingMeta, FilingsSummaryResponse, FilingSummary
from app.services import summarizer_service

logger = logging.getLogger(__name__)


async def resolve_cik(
    ticker: str, sec_client: SecClient, cache: Cache, settings: Settings
) -> tuple[str, str | None]:
    """Returns (cik, company_name) for a ticker, raising TickerNotFoundError if unknown."""
    ticker = ticker.upper()

    cik_map = await cache.get_or_set(
        key="cik_map",
        factory=sec_client.fetch_ticker_cik_map,
        ttl_seconds=settings.cik_map_cache_ttl_seconds,
    )

    entry = cik_map.get(ticker)
    if entry is None:
        raise TickerNotFoundError(ticker)

    return entry["cik"], entry["title"]


async def get_recent_filings(
    ticker: str,
    cik: str,
    sec_client: SecClient,
    cache: Cache,
    settings: Settings,
    forms: list[str],
    limit: int,
    lookback_months: int,
) -> list[FilingMeta]:
    submissions = await cache.get_or_set(
        key=f"submissions:{cik}",
        factory=lambda: sec_client.fetch_submissions(cik),
        ttl_seconds=settings.submissions_cache_ttl_seconds,
    )

    filings = select_recent_filings(
        submissions=submissions,
        cik=cik,
        forms=forms,
        limit=limit,
        lookback_months=lookback_months,
    )

    if not filings:
        raise NoRecentFilingsError(ticker)

    return filings


async def _get_filing_text(
    meta: FilingMeta, sec_client: SecClient, cache: Cache, settings: Settings
) -> str:
    async def factory() -> str:
        html = await sec_client.fetch_filing_document(str(meta.primary_document_url))
        return extract_text(html)

    return await cache.get_or_set(
        key=f"filing_raw:{meta.accession_number}",
        factory=factory,
        ttl_seconds=settings.filing_raw_cache_ttl_seconds,
    )


async def _get_filing_summary(
    meta: FilingMeta,
    sec_client: SecClient,
    openai_client: OpenAIClient,
    cache: Cache,
    settings: Settings,
) -> FilingSummary:
    async def factory() -> FilingSummary:
        text = await _get_filing_text(meta, sec_client, cache, settings)
        generated = await summarizer_service.summarize_filing(
            text=text,
            form_type=meta.form_type,
            filing_date=meta.filing_date.isoformat(),
            openai_client=openai_client,
        )
        return FilingSummary.from_generated(
            meta=meta, generated=generated, generated_at=datetime.now(tz=UTC)
        )

    return await cache.get_or_set(
        key=f"summary:{meta.accession_number}",
        factory=factory,
        ttl_seconds=settings.summary_cache_ttl_seconds,
    )


async def get_filings_summary(
    ticker: str,
    sec_client: SecClient,
    openai_client: OpenAIClient,
    cache: Cache,
    settings: Settings,
    forms: list[str],
    limit: int,
    lookback_months: int,
) -> FilingsSummaryResponse:
    cik, company_name = await resolve_cik(ticker, sec_client, cache, settings)

    filing_metas = await get_recent_filings(
        ticker=ticker,
        cik=cik,
        sec_client=sec_client,
        cache=cache,
        settings=settings,
        forms=forms,
        limit=limit,
        lookback_months=lookback_months,
    )

    summaries: list[FilingSummary] = []
    warnings: list[str] = []

    for meta in filing_metas:
        try:
            summary = await _get_filing_summary(
                meta, sec_client, openai_client, cache, settings
            )
            summaries.append(summary)
        except SummarizationError as exc:
            logger.warning(
                "Summarization failed for %s %s: %s", ticker, meta.accession_number, exc
            )
            warnings.append(
                f"Could not summarize {meta.form_type} filed {meta.filing_date}: {exc.detail}"
            )

    if not summaries:
        raise SummarizationError(f"All filing summarizations failed for {ticker}")

    return FilingsSummaryResponse(
        ticker=ticker.upper(),
        company_name=company_name,
        cik=cik,
        filings=summaries,
        warnings=warnings,
    )
