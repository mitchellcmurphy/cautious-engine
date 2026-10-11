// Synthetic data for local development (VITE_USE_MOCKS=true). Shapes mirror backend/app/schemas.

function hash(s: string) {
  let h = 2166136261
  for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619)
  return h >>> 0
}

const round2 = (n: number) => Math.round(n * 100) / 100
const lastPrice = new Map<string, number>()

const companyName = (ticker: string) =>
  HOLDINGS.find((h) => h.ticker === ticker)?.name ?? `${ticker} Holdings Inc.`

const previousClose = (ticker: string) => 20 + (hash(ticker) % 480)

/** Random walk per call; the mock market is always in its regular session. */
export function mockQuote(ticker: string) {
  const prevClose = previousClose(ticker)
  const prev = lastPrice.get(ticker) ?? prevClose * (1 + ((hash(ticker) % 200) - 100) / 5000)
  const price = round2(Math.max(1, prev * (1 + (Math.random() - 0.5) * 0.002)))
  lastPrice.set(ticker, price)
  return {
    ticker,
    company_name: companyName(ticker),
    price,
    currency: 'USD',
    change: round2(price - prevClose),
    change_percent: ((price - prevClose) / prevClose) * 100,
    previous_close: prevClose,
    market_state: 'REGULAR',
    as_of: new Date().toISOString(),
    source: 'yahoo_finance',
  }
}

export function mockFilingsSummary(ticker: string) {
  const edgar = (doc: string) => `https://www.sec.gov/Archives/edgar/data/0000000000/${doc}`
  return {
    ticker,
    company_name: `${ticker} Holdings Inc.`,
    cik: '0000000000',
    warnings: [],
    filings: [
      {
        meta: {
          form_type: '10-Q',
          filing_date: '2026-08-01',
          period_of_report: '2026-06-30',
          accession_number: '0000000000-26-000042',
          primary_document_url: edgar('q2-2026.htm'),
        },
        tldr: `Q2 beat guidance; ${ticker} raised its full-year outlook on stronger international demand.`,
        overview:
          'Revenue grew modestly year over year with gross margin expansion from mix shift toward services. Operating expenses rose on R&D investment. Liquidity remains strong and buybacks continued.',
        financial_highlights: [
          { label: 'Revenue', value: '$24.1B', period: 'Q2 FY2026' },
          { label: 'Net income', value: '$5.3B', period: 'Q2 FY2026' },
          { label: 'Diluted EPS', value: '$1.42', period: 'Q2 FY2026' },
          { label: 'Free cash flow', value: '$6.0B', period: 'Q2 FY2026' },
        ],
        notable_risks_or_changes: [
          'Supply chain constraints flagged for the second half',
          'New risk factor on AI regulation in the EU',
        ],
        sentiment: 'positive',
        confidence: 'high',
        generated_at: new Date().toISOString(),
      },
      {
        meta: {
          form_type: '10-K',
          filing_date: '2026-02-14',
          period_of_report: '2025-12-31',
          accession_number: '0000000000-26-000007',
          primary_document_url: edgar('fy2025-10k.htm'),
        },
        tldr: `Steady FY2025: revenue up 8%, margins expanded, and a new $5B buyback — but customer concentration remains a risk.`,
        overview:
          'Full-year growth was driven by the core segment. Management reiterated its focus on recurring revenue and capital returns, while noting foreign-exchange headwinds and pending regulatory reviews.',
        financial_highlights: [
          { label: 'Revenue', value: '$91.3B', period: 'FY2025' },
          { label: 'Operating margin', value: '29.4%', period: 'FY2025' },
          { label: 'Share repurchase authorization', value: '$5B', period: null },
        ],
        notable_risks_or_changes: [
          'Top 10 customers account for 31% of revenue',
          'Foreign exchange exposure',
          'Pending antitrust review in two jurisdictions',
        ],
        sentiment: 'mixed',
        confidence: 'medium',
        generated_at: new Date().toISOString(),
      },
    ],
  }
}

const HOLDINGS = [
  { ticker: 'AAPL', name: 'Apple Inc.', sector: 'Technology', shares: 1200, avg: 182.4 },
  { ticker: 'MSFT', name: 'Microsoft Corporation', sector: 'Technology', shares: 650, avg: 331.1 },
  { ticker: 'JNJ', name: 'Johnson & Johnson', sector: 'Health Care', shares: 900, avg: 161.75 },
  { ticker: 'JPM', name: 'JPMorgan Chase & Co.', sector: 'Financials', shares: 800, avg: 148.2 },
  { ticker: 'XOM', name: 'Exxon Mobil Corporation', sector: 'Energy', shares: 1500, avg: 118.9 },
  { ticker: 'PG', name: 'Procter & Gamble Co.', sector: 'Consumer Staples', shares: 700, avg: 171.3 },
]

function mockPosition(h: (typeof HOLDINGS)[number]) {
  const current_price = mockQuote(h.ticker).price
  const total_cost_basis = h.shares * h.avg
  const market_value = h.shares * current_price
  const unrealized_gain_loss = market_value - total_cost_basis
  return {
    ticker: h.ticker,
    name: h.name,
    sector: h.sector,
    total_shares: h.shares,
    total_cost_basis,
    avg_price_per_share: h.avg,
    current_price,
    market_value,
    unrealized_gain_loss,
    unrealized_gain_loss_pct: (unrealized_gain_loss / total_cost_basis) * 100,
  }
}

export function mockPortfolio() {
  const holdings = HOLDINGS.map(mockPosition)
  const cash = 250_000
  return {
    portfolio_id: 'firm-core',
    name: 'Firm Core Portfolio',
    as_of: new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' }),
    cash,
    holdings,
    total_market_value: holdings.reduce((s, h) => s + h.market_value, 0) + cash,
    total_cost_basis: holdings.reduce((s, h) => s + h.total_cost_basis, 0),
    total_unrealized_gain_loss: holdings.reduce((s, h) => s + h.unrealized_gain_loss, 0),
  }
}

const RATIONALE: Record<string, (t: string) => string> = {
  hold: (t) =>
    `${t} continues to execute: the latest 10-Q showed revenue and margin growth ahead of guidance. Valuation is stretched relative to peers, but fundamentals support keeping the position at its current weight.`,
  sell: (t) =>
    `${t} has run well above its cost basis while growth is decelerating and valuation sits near the top of its 5-year range. Trimming or exiting locks in gains ahead of rising execution risk.`,
  buy: (t) =>
    `${t} shows improving fundamentals in its latest filings with accelerating revenue and healthy free cash flow. Momentum supports initiating a position, sized conservatively given customer concentration risk.`,
  pass: (t) =>
    `${t}'s recent filings show slowing growth and negative momentum over the last six months. There isn't a compelling entry point relative to current holdings.`,
}

export function mockRecommendation(ticker: string) {
  const holding = HOLDINGS.find((h) => h.ticker === ticker)
  const filings = mockFilingsSummary(ticker).filings.map((f) => f.meta)
  const r = (hash(ticker) % 100) / 10 - 3
  const action = holding ? (r > 3 ? 'sell' : 'hold') : r > 0 ? 'buy' : 'pass'
  return {
    ticker,
    company_name: holding?.name ?? `${ticker} Holdings Inc.`,
    owned: Boolean(holding),
    action,
    rationale: RATIONALE[action](ticker),
    confidence: 'medium',
    key_factors: [
      'Revenue growth accelerated in the most recent quarter',
      'Operating margin expanded 120 bps year over year',
      'Customer concentration remains elevated',
      'Valuation above 5-year average multiple',
    ],
    performance: {
      return_1m: r,
      return_3m: r * 2.1,
      return_6m: r * 3.4 + 2,
      return_1y: ticker.length > 3 ? null : r * 5 + 8,
      as_of: new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' }),
    },
    position: holding ? mockPosition(holding) : null,
    based_on_filings: filings,
    generated_at: new Date().toISOString(),
  }
}
