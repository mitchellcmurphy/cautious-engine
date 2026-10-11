import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Quote } from '../api/types'
import { QuoteHeader } from './QuoteHeader'

const quote = (over: Partial<Quote> = {}): Quote => ({
  ticker: 'AAPL',
  company_name: 'Apple Inc.',
  price: 101,
  currency: 'USD',
  change: 1,
  change_percent: 1,
  previous_close: 100,
  market_state: 'REGULAR',
  as_of: '2026-10-09T19:59:00Z',
  source: 'yahoo_finance',
  ...over,
})

describe('QuoteHeader', () => {
  afterEach(() => vi.useRealTimers())

  it('shows price, change in percent units, and company', () => {
    render(<QuoteHeader quote={quote()} lastSuccessAt={Date.now()} failing={false} />)
    expect(screen.getByText('$101.00')).toBeInTheDocument()
    expect(screen.getByText(/\+1\.00 \(\+1\.00%\)/)).toBeInTheDocument()
    expect(screen.getByText(/Apple Inc\./)).toBeInTheDocument()
  })

  it('goes from Live to Delayed when polls stop succeeding', () => {
    vi.useFakeTimers({ now: 1_000_000 })
    render(<QuoteHeader quote={quote()} lastSuccessAt={999_000} failing={false} />)
    expect(screen.getByRole('status')).toHaveTextContent('Live')
    act(() => vi.advanceTimersByTime(6_000))
    expect(screen.getByRole('status')).toHaveTextContent('Delayed')
  })

  it('reports market state and failures', () => {
    const { rerender } = render(
      <QuoteHeader quote={quote({ market_state: 'CLOSED' })} lastSuccessAt={Date.now()} failing={false} />,
    )
    expect(screen.getByRole('status')).toHaveTextContent('Market closed')
    rerender(<QuoteHeader quote={quote()} lastSuccessAt={Date.now()} failing />)
    expect(screen.getByRole('status')).toHaveTextContent('Reconnecting')
  })
})
