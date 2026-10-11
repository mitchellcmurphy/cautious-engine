import { screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { mockRecommendation } from '../mocks/marketData'
import { renderWithFetch } from '../test/renderWithQuery'
import { RecommendationCard } from './RecommendationCard'

describe('RecommendationCard', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('shows the firm position for an owned ticker', async () => {
    renderWithFetch(<RecommendationCard ticker="AAPL" />, Response.json(mockRecommendation('AAPL')))
    expect(await screen.findByText('Held in portfolio')).toBeInTheDocument()
    expect(screen.getByText('Firm position')).toBeInTheDocument()
    expect(screen.getByText('Key factors')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /filed/ })).toHaveLength(2)
  })

  it('omits the position and shows missing returns as a dash for a non-owned ticker', async () => {
    renderWithFetch(<RecommendationCard ticker="NVDA" />, Response.json(mockRecommendation('NVDA')))
    expect(await screen.findByText('Not currently held')).toBeInTheDocument()
    expect(screen.queryByText('Firm position')).not.toBeInTheDocument()
    expect(screen.getByText(/^(Buy|Pass)$/)).toBeInTheDocument()
    expect(screen.getByText('1Y return').nextElementSibling).toHaveTextContent('—')
  })
})
