from app.clients.openai_client import OpenAIClient
from app.extraction.chunking import chunk_text, count_tokens
from app.schemas.filing import GeneratedSummaryContent

SYSTEM_PROMPT = (
    "You are a financial analyst assistant summarizing SEC filings for wealth "
    "management professionals. Be precise and base every statement only on the "
    "provided text — never speculate or fabricate figures. Where the text does "
    "not contain a piece of information, say so (use empty lists / 'unknown') "
    "rather than guessing."
)

# gpt-4o-mini has a 128k context window; these thresholds leave ample room for
# the system prompt, schema, and response while keeping most 10-Qs single-pass
# and routing larger 10-Ks (and any text over ~45k tokens) to map-reduce.
SINGLE_PASS_TOKEN_LIMIT = 20_000
MAP_CHUNK_TOKEN_LIMIT = 6_000

MAP_PROMPT_TEMPLATE = """\
This is an excerpt from a {form_type} filed {filing_date}. Extract only what is \
explicitly stated in THIS excerpt as short bullet points, grouped under these \
headings: Overview, Financial Highlights, Risks/Changes. Do not infer anything \
about other parts of the filing you have not seen. If a heading has nothing \
relevant in this excerpt, omit it.

EXCERPT:
{excerpt}
"""

SINGLE_PASS_PROMPT_TEMPLATE = """\
Summarize this {form_type} filed {filing_date} into the required structured \
format. Populate every field; use "unknown"/empty lists where the filing text \
does not provide enough information rather than guessing.

FILING TEXT:
{text}
"""

REDUCE_PROMPT_TEMPLATE = """\
Below are bullet-point notes extracted from successive excerpts of a single \
{form_type} filed {filing_date}. Synthesize them into the required structured \
format. Populate every field; use "unknown"/empty lists where the notes don't \
provide enough information rather than guessing.

NOTES:
{notes}
"""


async def summarize_filing(
    text: str,
    form_type: str,
    filing_date: str,
    openai_client: OpenAIClient,
) -> GeneratedSummaryContent:
    if count_tokens(text) <= SINGLE_PASS_TOKEN_LIMIT:
        return await _summarize_single_pass(text, form_type, filing_date, openai_client)
    return await _summarize_map_reduce(text, form_type, filing_date, openai_client)


async def _summarize_single_pass(
    text: str, form_type: str, filing_date: str, openai_client: OpenAIClient
) -> GeneratedSummaryContent:
    prompt = SINGLE_PASS_PROMPT_TEMPLATE.format(
        form_type=form_type, filing_date=filing_date, text=text
    )
    return await openai_client.complete_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        schema_model=GeneratedSummaryContent,
    )


async def _summarize_map_reduce(
    text: str, form_type: str, filing_date: str, openai_client: OpenAIClient
) -> GeneratedSummaryContent:
    chunks = chunk_text(text, max_tokens=MAP_CHUNK_TOKEN_LIMIT)

    notes = []
    for chunk in chunks:
        prompt = MAP_PROMPT_TEMPLATE.format(
            form_type=form_type, filing_date=filing_date, excerpt=chunk
        )
        note = await openai_client.complete_text(SYSTEM_PROMPT, prompt)
        notes.append(note)

    combined_notes = "\n\n".join(notes)
    reduce_prompt = REDUCE_PROMPT_TEMPLATE.format(
        form_type=form_type, filing_date=filing_date, notes=combined_notes
    )
    return await openai_client.complete_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=reduce_prompt,
        schema_model=GeneratedSummaryContent,
    )
