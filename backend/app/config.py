from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "ai-improv-backend"

    sec_contact_email: str
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    quote_cache_ttl_seconds: int = 45
    cik_map_cache_ttl_seconds: int = 86400
    submissions_cache_ttl_seconds: int = 3600
    filing_raw_cache_ttl_seconds: int = 604800
    summary_cache_ttl_seconds: int = 86400

    max_filings_per_request: int = 5
    sec_requests_per_second: int = 8

    portfolio_data_path: Path = Field(
        default=REPO_ROOT / "data" / "sample_portfolio.json"
    )
    portfolio_cache_ttl_seconds: int = 86400
    performance_cache_ttl_seconds: int = 3600
    recommendation_cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=".env", env_prefix="")
