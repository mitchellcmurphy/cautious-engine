from fastapi import APIRouter, Depends

from app.caching.base import Cache
from app.config import Settings
from app.deps import get_cache, get_settings
from app.schemas.portfolio import PortfolioResponse
from app.services import portfolio_service

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
async def read_portfolio(
    cache: Cache = Depends(get_cache),
    settings: Settings = Depends(get_settings),
) -> PortfolioResponse:
    return await portfolio_service.get_portfolio(cache, settings)
