from app.caching.base import Cache
from app.clients import portfolio_store
from app.config import Settings
from app.schemas.portfolio import HoldingPosition, PortfolioResponse
from app.services import quote_service


async def _load_raw_portfolio(cache: Cache, settings: Settings) -> dict:
    return await cache.get_or_set(
        key="portfolio_raw",
        factory=lambda: _read_portfolio_file(settings),
        ttl_seconds=settings.portfolio_cache_ttl_seconds,
    )


async def _read_portfolio_file(settings: Settings) -> dict:
    return portfolio_store.load_portfolio(settings.portfolio_data_path)


async def _build_position(
    holding: dict, cache: Cache, settings: Settings
) -> HoldingPosition:
    total_shares, total_cost_basis, avg_price_per_share = (
        portfolio_store.aggregate_lots(holding)
    )
    quote = await quote_service.get_quote(holding["ticker"], cache, settings)

    market_value = total_shares * quote.price
    unrealized_gain_loss = market_value - total_cost_basis
    unrealized_gain_loss_pct = (
        unrealized_gain_loss / total_cost_basis * 100 if total_cost_basis else 0.0
    )

    return HoldingPosition(
        ticker=holding["ticker"],
        name=holding["name"],
        sector=holding["sector"],
        total_shares=total_shares,
        total_cost_basis=total_cost_basis,
        avg_price_per_share=avg_price_per_share,
        current_price=quote.price,
        market_value=market_value,
        unrealized_gain_loss=unrealized_gain_loss,
        unrealized_gain_loss_pct=unrealized_gain_loss_pct,
    )


async def get_portfolio(cache: Cache, settings: Settings) -> PortfolioResponse:
    raw = await _load_raw_portfolio(cache, settings)

    holdings = [await _build_position(h, cache, settings) for h in raw["holdings"]]

    total_market_value = sum(h.market_value for h in holdings) + raw["cash"]["amount"]
    total_cost_basis = sum(h.total_cost_basis for h in holdings)
    total_unrealized_gain_loss = sum(h.unrealized_gain_loss for h in holdings)

    return PortfolioResponse(
        portfolio_id=raw["portfolio_id"],
        name=raw["name"],
        as_of=raw["as_of"],
        cash=raw["cash"]["amount"],
        holdings=holdings,
        total_market_value=total_market_value,
        total_cost_basis=total_cost_basis,
        total_unrealized_gain_loss=total_unrealized_gain_loss,
    )


async def get_position(
    ticker: str, cache: Cache, settings: Settings
) -> HoldingPosition | None:
    raw = await _load_raw_portfolio(cache, settings)
    holding = portfolio_store.find_holding(raw, ticker)
    if holding is None:
        return None
    return await _build_position(holding, cache, settings)
