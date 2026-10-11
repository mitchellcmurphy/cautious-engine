import { useQuery } from '@tanstack/react-query'
import { fetchRecommendation } from '../api/stocks'

export function useRecommendation(ticker: string) {
  return useQuery({
    queryKey: ['recommendation', ticker],
    queryFn: ({ signal }) => fetchRecommendation(ticker, signal),
    // LLM-generated and cached server-side for an hour; don't re-run it on every visit.
    staleTime: 30 * 60_000,
    retry: false,
  })
}
