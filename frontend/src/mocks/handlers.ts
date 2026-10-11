import { delay, http, HttpResponse } from 'msw'
import { mockFilingsSummary, mockPortfolio, mockQuote, mockRecommendation } from './marketData'

// "ZZZZ" simulates an unknown ticker; "NOFL" a ticker with no recent filings.
const error = (status: number, error: string, message: string) =>
  HttpResponse.json({ error, message, detail: null }, { status })

export const handlers = [
  http.get('/quotes/:ticker', async ({ params }) => {
    await delay(150)
    const ticker = String(params.ticker).toUpperCase()
    if (ticker === 'ZZZZ') return error(404, 'ticker_not_found', `Ticker '${ticker}' was not found.`)
    return HttpResponse.json(mockQuote(ticker))
  }),

  http.get('/filings/:ticker/summary', async ({ params }) => {
    await delay(2500) // real summaries take tens of seconds when uncached
    const ticker = String(params.ticker).toUpperCase()
    if (ticker === 'ZZZZ') return error(404, 'ticker_not_found', `Ticker '${ticker}' was not found.`)
    if (ticker === 'NOFL') return error(404, 'no_recent_filings', `No recent 10-K/10-Q filings found for '${ticker}'.`)
    return HttpResponse.json(mockFilingsSummary(ticker))
  }),

  http.get('/portfolio', async () => {
    await delay(300)
    return HttpResponse.json(mockPortfolio())
  }),

  http.get('/recommendations/:ticker', async ({ params }) => {
    await delay(3000) // LLM-generated
    const ticker = String(params.ticker).toUpperCase()
    if (ticker === 'ZZZZ') return error(404, 'ticker_not_found', `Ticker '${ticker}' was not found.`)
    return HttpResponse.json(mockRecommendation(ticker))
  }),
]
