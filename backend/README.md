# Backend

FastAPI service providing current stock quotes (Yahoo Finance) and AI-generated
summaries of recent SEC 10-K/10-Q filings (SEC EDGAR + OpenAI).

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in SEC_CONTACT_EMAIL and OPENAI_API_KEY
```

`SEC_CONTACT_EMAIL` is required by SEC's fair-access policy (sent as part of
the `User-Agent` header on every EDGAR request) — use a real contact address
for your firm.

## Run

```bash
uvicorn app.main:app --reload
```

## Endpoints

### `GET /quotes/{ticker}`

```bash
curl -s http://localhost:8000/quotes/AAPL | python -m json.tool
```

### `GET /filings/{ticker}/summary`

AI-summarizes the most recent 10-K/10-Q filings for a ticker. Query params:
`forms` (default `10-K` + `10-Q`), `limit` (default `2`, max `5`),
`lookback_months` (default `18`).

```bash
curl -s http://localhost:8000/filings/AAPL/summary | python -m json.tool
```

The first call for a given filing is slow (fetches + extracts the filing from
SEC EDGAR, then summarizes via OpenAI — tens of seconds for a large 10-K).
Repeat calls within the cache TTL return near-instantly.

## Tests

```bash
pytest
```

All tests run against fixtures/mocks — no live network calls or API keys needed.
