from app.schemas.filing import GeneratedSummaryContent
from app.services import summarizer_service

SAMPLE_SUMMARY = GeneratedSummaryContent(
    tldr="A short summary.",
    overview="An overview.",
    financial_highlights=[],
    notable_risks_or_changes=[],
    sentiment="neutral",
    confidence="medium",
)


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.structured_calls: list[str] = []
        self.text_calls: list[str] = []

    async def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        self.text_calls.append(user_prompt)
        return "- Overview: noted\n- Financial Highlights: noted"

    async def complete_structured(
        self, system_prompt: str, user_prompt: str, schema_model
    ):
        self.structured_calls.append(user_prompt)
        return SAMPLE_SUMMARY


async def test_short_text_uses_single_pass():
    fake = _FakeOpenAIClient()
    short_text = "This is a short filing excerpt."

    result = await summarizer_service.summarize_filing(
        text=short_text, form_type="10-Q", filing_date="2026-07-31", openai_client=fake
    )

    assert result == SAMPLE_SUMMARY
    assert len(fake.structured_calls) == 1
    assert len(fake.text_calls) == 0
    assert short_text in fake.structured_calls[0]


async def test_long_text_uses_map_reduce():
    fake = _FakeOpenAIClient()
    # one word is ~1 token with this tokenizer; force well past SINGLE_PASS_TOKEN_LIMIT
    long_text = (
        "word " * (summarizer_service.SINGLE_PASS_TOKEN_LIMIT + 5000) + "\n\n"
    ) * 1

    result = await summarizer_service.summarize_filing(
        text=long_text, form_type="10-K", filing_date="2026-10-31", openai_client=fake
    )

    assert result == SAMPLE_SUMMARY
    assert len(fake.text_calls) >= 1  # map step(s) happened
    assert len(fake.structured_calls) == 1  # exactly one reduce step
