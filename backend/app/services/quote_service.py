from app.caching.base import Cache
from app.clients import yahoo_client
from app.config import Settings
from app.schemas.quote import QuoteResponse


async def get_quote(ticker: str, cache: Cache, settings: Settings) -> QuoteResponse:
    ticker = ticker.upper()

    async def factory() -> QuoteResponse:
        raw = await yahoo_client.get_quote(ticker)
        return QuoteResponse(
            ticker=raw.ticker,
            company_name=raw.company_name,
            price=raw.price,
            currency=raw.currency,
            change=raw.change,
            change_percent=raw.change_percent,
            previous_close=raw.previous_close,
            market_state=raw.market_state,
            as_of=raw.as_of,
            source="yahoo_finance",
        )

    return await cache.get_or_set(
        key=f"quote:{ticker}",
        factory=factory,
        ttl_seconds=settings.quote_cache_ttl_seconds,
    )
