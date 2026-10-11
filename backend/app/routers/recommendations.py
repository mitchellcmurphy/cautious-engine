from fastapi import APIRouter, Depends

from app.caching.base import Cache
from app.clients.openai_client import OpenAIClient
from app.clients.sec_client import SecClient
from app.config import Settings
from app.deps import get_cache, get_openai_client, get_sec_client, get_settings
from app.schemas.recommendation import RecommendationResponse
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{ticker}", response_model=RecommendationResponse)
async def read_recommendation(
    ticker: str,
    sec_client: SecClient = Depends(get_sec_client),
    openai_client: OpenAIClient = Depends(get_openai_client),
    cache: Cache = Depends(get_cache),
    settings: Settings = Depends(get_settings),
) -> RecommendationResponse:
    return await recommendation_service.get_recommendation(
        ticker=ticker,
        sec_client=sec_client,
        openai_client=openai_client,
        cache=cache,
        settings=settings,
    )
