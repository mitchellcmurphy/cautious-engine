import { useState } from 'react'
import type { PricePoint, Quote } from '../api/types'

// ~one trading session at 1 point/sec.
const MAX_POINTS = 6.5 * 60 * 60

/**
 * Builds an intraday series from polled quotes, one point per distinct `as_of`.
 * There's no history endpoint yet, so the series starts when the page opens.
 * Callers should key the owning component by ticker so the series resets.
 */
export function useQuoteSeries(quote: Quote | undefined): PricePoint[] {
  const [points, setPoints] = useState<PricePoint[]>([])
  const last = points.at(-1)

  // Adjusting state during render (not in an effect) avoids an extra paint per tick.
  if (quote && (!last || Date.parse(quote.as_of) > Date.parse(last.t))) {
    setPoints([...points, { t: quote.as_of, price: quote.price }].slice(-MAX_POINTS))
  }
  return points
}
