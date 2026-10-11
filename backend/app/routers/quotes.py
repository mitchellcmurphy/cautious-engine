from fastapi import APIRouter, Depends

from app.caching.base import Cache
from app.config import Settings
from app.deps import get_cache, get_settings
from app.schemas.quote import QuoteResponse
from app.services import quote_service

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/{ticker}", response_model=QuoteResponse)
async def read_quote(
    ticker: str,
    cache: Cache = Depends(get_cache),
    settings: Settings = Depends(get_settings),
) -> QuoteResponse:
    return await quote_service.get_quote(ticker, cache, settings)
