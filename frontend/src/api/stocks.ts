import { getJson } from './client'
import { filingsSummarySchema, portfolioSchema, quoteSchema, recommendationSchema } from './types'

const enc = encodeURIComponent

export const fetchQuote = (ticker: string, signal?: AbortSignal) =>
  getJson(`/quotes/${enc(ticker)}`, quoteSchema, signal)

export const fetchFilingsSummary = (ticker: string, signal?: AbortSignal) =>
  getJson(`/filings/${enc(ticker)}/summary`, filingsSummarySchema, signal)

export const fetchPortfolio = (signal?: AbortSignal) => getJson('/portfolio', portfolioSchema, signal)

export const fetchRecommendation = (ticker: string, signal?: AbortSignal) =>
  getJson(`/recommendations/${enc(ticker)}`, recommendationSchema, signal)
