import { useQuery } from '@tanstack/react-query'
import { ApiError } from '../api/client'
import { fetchQuote } from '../api/stocks'

export const QUOTE_POLL_MS = 1000

export function useQuote(ticker: string) {
  return useQuery({
    queryKey: ['quote', ticker],
    queryFn: ({ signal }) => fetchQuote(ticker, signal),
    // Stop polling an unknown ticker; keep polling through transient failures.
    refetchInterval: (query) => {
      const err = query.state.error
      return err instanceof ApiError && err.status === 404 ? false : QUOTE_POLL_MS
    },
    refetchIntervalInBackground: false,
  })
}
