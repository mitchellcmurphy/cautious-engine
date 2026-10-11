import { screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { mockFilingsSummary } from '../mocks/marketData'
import { renderWithFetch } from '../test/renderWithQuery'
import { FilingsSection } from './FilingsSection'

describe('FilingsSection', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('renders each filing summary', async () => {
    renderWithFetch(<FilingsSection ticker="AAPL" />, Response.json(mockFilingsSummary('AAPL')))
    expect(await screen.findByText(/Quarterly report/)).toBeInTheDocument()
    expect(screen.getByText(/Annual report/)).toBeInTheDocument()
    expect(screen.getByText('$24.1B')).toBeInTheDocument()
    expect(screen.getByText('Filed Aug 1, 2026 · Period ending Jun 30, 2026')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /View on EDGAR/ })).toHaveLength(2)
  })

  it('shows the API message when there are no recent filings', async () => {
    renderWithFetch(
      <FilingsSection ticker="AAPL" />,
      Response.json(
        { error: 'no_recent_filings', message: "No recent 10-K/10-Q filings found for 'AAPL'." },
        { status: 404 },
      ),
    )
    expect(await screen.findByText("No recent 10-K/10-Q filings found for 'AAPL'.")).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })
})
