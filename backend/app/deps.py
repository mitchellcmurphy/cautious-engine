from functools import lru_cache

import httpx

from app.caching.base import Cache
from app.caching.memory import InMemoryTTLCache
from app.clients.openai_client import OpenAIClient
from app.clients.sec_client import SecClient
from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_cache() -> Cache:
    return InMemoryTTLCache()


@lru_cache
def get_http_client() -> httpx.AsyncClient:
    settings = get_settings()
    headers = {"User-Agent": f"{settings.app_name} ({settings.sec_contact_email})"}
    return httpx.AsyncClient(headers=headers)


@lru_cache
def get_sec_client() -> SecClient:
    settings = get_settings()
    return SecClient(
        http_client=get_http_client(),
        requests_per_second=settings.sec_requests_per_second,
    )


@lru_cache
def get_openai_client() -> OpenAIClient:
    settings = get_settings()
    return OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model)
