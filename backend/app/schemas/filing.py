from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl


class FilingMeta(BaseModel):
    form_type: Literal["10-K", "10-Q"]
    filing_date: date
    period_of_report: date | None
    accession_number: str
    primary_document_url: HttpUrl


class FinancialHighlight(BaseModel):
    label: str
    value: str
    period: str | None = None


class GeneratedSummaryContent(BaseModel):
    """The subset of FilingSummary that the LLM is asked to produce.

    Kept separate from FilingSummary because `meta`/`generated_at` are
    populated by our own code (never the model), to avoid date hallucination.
    """

    tldr: str
    overview: str
    financial_highlights: list[FinancialHighlight]
    notable_risks_or_changes: list[str]
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    confidence: Literal["high", "medium", "low"]


class FilingSummary(BaseModel):
    meta: FilingMeta
    tldr: str
    overview: str
    financial_highlights: list[FinancialHighlight]
    notable_risks_or_changes: list[str]
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    confidence: Literal["high", "medium", "low"]
    generated_at: datetime

    @classmethod
    def from_generated(
        cls,
        meta: FilingMeta,
        generated: GeneratedSummaryContent,
        generated_at: datetime,
    ) -> "FilingSummary":
        return cls(meta=meta, generated_at=generated_at, **generated.model_dump())


class FilingsSummaryResponse(BaseModel):
    ticker: str
    company_name: str | None
    cik: str
    filings: list[FilingSummary]
    warnings: list[str] = []
