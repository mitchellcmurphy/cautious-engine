import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.core.exceptions import (
    NoRecentFilingsError,
    SummarizationError,
    TickerNotFoundError,
    UpstreamServiceError,
)
from app.routers import filings, portfolio, quotes, recommendations
from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)

settings = Settings()

app = FastAPI(title=settings.app_name)

app.include_router(quotes.router)
app.include_router(filings.router)
app.include_router(portfolio.router)
app.include_router(recommendations.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(TickerNotFoundError)
async def handle_ticker_not_found(
    request: Request, exc: TickerNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="ticker_not_found",
            message=f"Ticker '{exc.ticker}' was not found.",
        ).model_dump(),
    )


@app.exception_handler(NoRecentFilingsError)
async def handle_no_recent_filings(
    request: Request, exc: NoRecentFilingsError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="no_recent_filings",
            message=f"No recent 10-K/10-Q filings found for '{exc.ticker}'.",
        ).model_dump(),
    )


@app.exception_handler(UpstreamServiceError)
async def handle_upstream_service_error(
    request: Request, exc: UpstreamServiceError
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(
            error="upstream_service_error",
            message=f"Request to {exc.service} failed.",
            detail=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(SummarizationError)
async def handle_summarization_error(
    request: Request, exc: SummarizationError
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(
            error="summarization_failed",
            message="Failed to generate a filing summary.",
            detail=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error processing request", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred.",
        ).model_dump(),
    )


# In the container image the built frontend is copied to STATIC_DIR and served
# from the same origin as the API. Mounted last so the API routes above win.
# Locally (no build present) this is skipped and Vite serves the frontend.
_static_dir = Path(
    os.environ.get("STATIC_DIR", Path(__file__).parent.parent / "static")
)
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="frontend")
