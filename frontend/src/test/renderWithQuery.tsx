import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { vi } from 'vitest'

/** Renders with a fresh QueryClient and a stubbed fetch that always returns `response`. */
export function renderWithFetch(ui: ReactElement, response: Response) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}
