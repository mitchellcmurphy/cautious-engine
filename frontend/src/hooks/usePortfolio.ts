import { useQuery } from '@tanstack/react-query'
import { fetchPortfolio } from '../api/stocks'

export function usePortfolio() {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: ({ signal }) => fetchPortfolio(signal),
    // Prices come from the quote cache server-side; a minute is fresh enough for a holdings view.
    staleTime: 60_000,
    refetchInterval: 60_000,
  })
}
