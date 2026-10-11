from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.caching.base import Cache
from app.clients.openai_client import OpenAIClient
from app.clients.sec_client import SecClient
from app.config import Settings
from app.deps import get_cache, get_openai_client, get_sec_client, get_settings
from app.schemas.filing import FilingsSummaryResponse
from app.services import filing_service

router = APIRouter(prefix="/filings", tags=["filings"])


@router.get("/{ticker}/summary", response_model=FilingsSummaryResponse)
async def read_filings_summary(
    ticker: str,
    forms: list[Literal["10-K", "10-Q"]] = Query(default=["10-K", "10-Q"]),
    limit: int = Query(default=2, ge=1),
    lookback_months: int = Query(default=18, ge=1, le=60),
    sec_client: SecClient = Depends(get_sec_client),
    openai_client: OpenAIClient = Depends(get_openai_client),
    cache: Cache = Depends(get_cache),
    settings: Settings = Depends(get_settings),
) -> FilingsSummaryResponse:
    return await filing_service.get_filings_summary(
        ticker=ticker,
        sec_client=sec_client,
        openai_client=openai_client,
        cache=cache,
        settings=settings,
        forms=forms,
        limit=min(limit, settings.max_filings_per_request),
        lookback_months=lookback_months,
    )
