import { fireEvent, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { mockPortfolio } from '../mocks/marketData'
import { renderWithFetch } from '../test/renderWithQuery'
import { PortfolioTable } from './PortfolioTable'

describe('PortfolioTable', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('lists holdings and selects one on click', async () => {
    const onSelect = vi.fn()
    renderWithFetch(<PortfolioTable selected="MSFT" onSelect={onSelect} />, Response.json(mockPortfolio()))

    expect(await screen.findByText('Firm Core Portfolio')).toBeInTheDocument()
    expect(screen.getAllByRole('row')).toHaveLength(1 + 6) // header + holdings
    expect(screen.getByRole('button', { name: /Load MSFT/ }).closest('tr')).toHaveAttribute('aria-selected', 'true')

    fireEvent.click(screen.getByText('Johnson & Johnson'))
    expect(onSelect).toHaveBeenCalledWith('JNJ')
    fireEvent.click(screen.getByRole('button', { name: /Load XOM/ }))
    expect(onSelect).toHaveBeenLastCalledWith('XOM')
    expect(onSelect).toHaveBeenCalledTimes(2)
  })
})
