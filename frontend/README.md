# Stock Ramp-Up — frontend

React + TypeScript (Vite) UI: pick a holding from the firm portfolio (or search any ticker) →
current quote (polled every second) with a live price chart, an AI buy/sell/hold/pass
recommendation, and AI summaries of the latest 10-K / 10-Q filings.

```bash
npm install
npm run dev        # http://localhost:5173, proxies API paths to FastAPI on :8000
npm run dev:mock   # synthetic data via MSW — no backend needed
npm test           # vitest
npm run build
```

Point the proxy elsewhere with `API_PROXY_TARGET=http://host:port npm run dev`, or bypass it
with `VITE_API_BASE_URL`.

## Backend endpoints used

Schemas mirror `backend/app/schemas` and live in `src/api/types.ts` (zod-validated).

| Endpoint | Used for |
|---|---|
| `GET /quotes/{ticker}` | Header + chart. Polled every 1s; a new chart point is added whenever `as_of` changes. |
| `GET /filings/{ticker}/summary` | Filing cards. Not retried on failure (a cold summary takes tens of seconds). |
| `GET /portfolio` | Holdings table; clicking a row loads that ticker. Refreshed every 60s. |
| `GET /recommendations/{ticker}` | Recommendation card (action, rationale, key factors, returns, firm position if held, source filings). Not retried on failure. |

Errors use the backend's `{ error, message, detail }` body; `message` is shown to the user and
`error: "no_recent_filings"` renders as an empty state rather than a failure.

There's no history endpoint yet, so the chart starts empty and fills in from polled quotes while
the page is open.

## Layout

```
src/
  api/          client.ts (fetch + errors), stocks.ts (endpoints), types.ts (schemas)
  hooks/        useQuote (1s polling), useQuoteSeries (builds chart points), useFilings,
                usePortfolio, useRecommendation, useNow
  components/   PortfolioTable
                StockView → QuoteHeader, PriceChart (lightweight-charts), RecommendationCard,
                            FilingsSection → FilingCard
  mocks/        MSW handlers + synthetic data ("ZZZZ" = unknown ticker, "NOFL" = no filings)
```
