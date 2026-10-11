import { useQuery } from '@tanstack/react-query'
import { fetchFilingsSummary } from '../api/stocks'

export function useFilings(ticker: string) {
  return useQuery({
    queryKey: ['filings', ticker],
    queryFn: ({ signal }) => fetchFilingsSummary(ticker, signal),
    // Latest 10-K/10-Q change rarely, and a cold summary takes tens of seconds.
    staleTime: 30 * 60_000,
    retry: false,
  })
}
