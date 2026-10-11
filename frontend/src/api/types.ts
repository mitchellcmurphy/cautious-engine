import { z } from 'zod'

// Mirrors backend/app/schemas — keep in sync when the API changes.

/** GET /quotes/{ticker} */
export const quoteSchema = z.object({
  ticker: z.string(),
  company_name: z.string().nullable(),
  price: z.number(),
  currency: z.string(),
  change: z.number(),
  change_percent: z.number(), // percent units: 1.23 means 1.23%
  previous_close: z.number(),
  market_state: z.string(), // Yahoo marketState: REGULAR, PRE, POST, CLOSED, ...
  as_of: z.string(), // ISO 8601
  source: z.string(),
})

export const filingMetaSchema = z.object({
  form_type: z.enum(['10-K', '10-Q']),
  filing_date: z.string(), // YYYY-MM-DD
  period_of_report: z.string().nullable(),
  accession_number: z.string(),
  primary_document_url: z.string(),
})

const financialHighlightSchema = z.object({
  label: z.string(),
  value: z.string(),
  period: z.string().nullable().optional(),
})

export const filingSummarySchema = z.object({
  meta: filingMetaSchema,
  tldr: z.string(),
  overview: z.string(),
  financial_highlights: z.array(financialHighlightSchema),
  notable_risks_or_changes: z.array(z.string()),
  sentiment: z.enum(['positive', 'neutral', 'negative', 'mixed']),
  confidence: z.enum(['high', 'medium', 'low']),
  generated_at: z.string(),
})

/** GET /filings/{ticker}/summary */
export const filingsSummarySchema = z.object({
  ticker: z.string(),
  company_name: z.string().nullable(),
  cik: z.string(),
  filings: z.array(filingSummarySchema),
  warnings: z.array(z.string()).default([]),
})

export const holdingPositionSchema = z.object({
  ticker: z.string(),
  name: z.string(),
  sector: z.string(),
  total_shares: z.number(),
  total_cost_basis: z.number(),
  avg_price_per_share: z.number(),
  current_price: z.number(),
  market_value: z.number(),
  unrealized_gain_loss: z.number(),
  unrealized_gain_loss_pct: z.number(), // percent units
})

/** GET /portfolio */
export const portfolioSchema = z.object({
  portfolio_id: z.string(),
  name: z.string(),
  as_of: z.string(), // YYYY-MM-DD
  cash: z.number(),
  holdings: z.array(holdingPositionSchema),
  total_market_value: z.number(), // includes cash
  total_cost_basis: z.number(),
  total_unrealized_gain_loss: z.number(),
})

const performanceSchema = z.object({
  // Percent units; null when the history doesn't go back far enough.
  return_1m: z.number().nullable(),
  return_3m: z.number().nullable(),
  return_6m: z.number().nullable(),
  return_1y: z.number().nullable(),
  as_of: z.string(),
})

/** GET /recommendations/{ticker} */
export const recommendationSchema = z.object({
  ticker: z.string(),
  company_name: z.string().nullable(),
  owned: z.boolean(),
  action: z.enum(['buy', 'sell', 'hold', 'pass']),
  rationale: z.string(),
  confidence: z.enum(['high', 'medium', 'low']),
  key_factors: z.array(z.string()),
  performance: performanceSchema,
  position: holdingPositionSchema.nullable(),
  based_on_filings: z.array(filingMetaSchema),
  generated_at: z.string(),
})

/** App-level errors: { error, message, detail? }. FastAPI validation errors use { detail }. */
export const errorBodySchema = z.object({
  error: z.string().optional(),
  message: z.string().optional(),
  detail: z.unknown().optional(),
})

export type Quote = z.infer<typeof quoteSchema>
export type FilingSummary = z.infer<typeof filingSummarySchema>
export type FilingsSummary = z.infer<typeof filingsSummarySchema>
export type HoldingPosition = z.infer<typeof holdingPositionSchema>
export type Portfolio = z.infer<typeof portfolioSchema>
export type Recommendation = z.infer<typeof recommendationSchema>

/** A point on the client-built intraday series. */
export interface PricePoint {
  t: string // ISO 8601
  price: number
}
