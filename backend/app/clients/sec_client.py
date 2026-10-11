import asyncio
from datetime import date, timedelta

import httpx

from app.core.exceptions import (
    UpstreamServiceError,
)
from app.schemas.filing import FilingMeta

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


class SecClient:
    """Thin client for SEC EDGAR's public JSON APIs.

    All requests must carry a descriptive User-Agent per SEC's fair-access
    policy, and stay under ~10 req/s — both enforced here via a shared
    httpx.AsyncClient and a semaphore.
    """

    def __init__(
        self, http_client: httpx.AsyncClient, requests_per_second: int
    ) -> None:
        self._http = http_client
        self._semaphore = asyncio.Semaphore(requests_per_second)

    async def _get_json(self, url: str) -> dict:
        async with self._semaphore:
            try:
                response = await self._http.get(url, timeout=10)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("sec_edgar", str(exc)) from exc
            return response.json()

    async def _get_text(self, url: str) -> str:
        async with self._semaphore:
            try:
                response = await self._http.get(url, timeout=10)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise UpstreamServiceError("sec_edgar", str(exc)) from exc
            return response.text

    async def fetch_ticker_cik_map(self) -> dict[str, dict[str, str]]:
        """Returns {TICKER: {"cik": "0000320193", "title": "Apple Inc."}}."""
        data = await self._get_json(TICKERS_URL)
        return {
            entry["ticker"].upper(): {
                "cik": str(entry["cik_str"]).zfill(10),
                "title": entry["title"],
            }
            for entry in data.values()
        }

    async def fetch_submissions(self, cik: str) -> dict:
        return await self._get_json(SUBMISSIONS_URL.format(cik=cik))

    async def fetch_filing_document(self, url: str) -> str:
        return await self._get_text(url)


def select_recent_filings(
    submissions: dict,
    cik: str,
    forms: list[str],
    limit: int,
    lookback_months: int,
) -> list[FilingMeta]:
    recent = submissions["filings"]["recent"]
    cutoff = date.today() - timedelta(days=lookback_months * 30)
    cik_int = int(cik)

    candidates: list[FilingMeta] = []
    for i, form in enumerate(recent["form"]):
        if form not in forms:
            continue
        filing_date = date.fromisoformat(recent["filingDate"][i])
        if filing_date < cutoff:
            continue

        report_date_raw = recent.get("reportDate", [None] * len(recent["form"]))[i]
        report_date = date.fromisoformat(report_date_raw) if report_date_raw else None

        accession_number = recent["accessionNumber"][i]
        accession_no_dashes = accession_number.replace("-", "")
        primary_document = recent["primaryDocument"][i]
        document_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{accession_no_dashes}/{primary_document}"
        )

        candidates.append(
            FilingMeta(
                form_type=form,
                filing_date=filing_date,
                period_of_report=report_date,
                accession_number=accession_number,
                primary_document_url=document_url,
            )
        )

    candidates.sort(key=lambda f: f.filing_date, reverse=True)
    return candidates[:limit]
