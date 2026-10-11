import { ApiError } from '../api/client'
import { useQuote } from '../hooks/useQuote'
import { useQuoteSeries } from '../hooks/useQuoteSeries'
import { Card } from './Card'
import { FilingsSection } from './FilingsSection'
import { PriceChart } from './PriceChart'
import { QuoteHeader } from './QuoteHeader'
import { RecommendationCard } from './RecommendationCard'
import { ErrorState, Skeleton } from './states'

/** Render with key={ticker} so the collected price series resets when the ticker changes. */
export function StockView({ ticker }: { ticker: string }) {
  const quote = useQuote(ticker)
  const points = useQuoteSeries(quote.data)

  return (
    <div className="space-y-6">
      <Card>
        {quote.data ? (
          <>
            <QuoteHeader quote={quote.data} lastSuccessAt={quote.dataUpdatedAt} failing={quote.isError} />
            <div className="mt-6">
              <p className="mb-2 text-xs text-(--text-muted)">Live prices since this page was opened</p>
              <PriceChart
                ticker={ticker}
                points={points}
                currency={quote.data.currency}
                marketOpen={quote.data.market_state === 'REGULAR'}
              />
            </div>
          </>
        ) : quote.isError ? (
          <ErrorState
            message={
              quote.error instanceof ApiError && quote.error.status === 404
                ? quote.error.message
                : `Couldn't load quote: ${quote.error.message}`
            }
            onRetry={() => quote.refetch()}
          />
        ) : (
          <div className="space-y-3" aria-busy="true">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-12 w-56" />
            <Skeleton className="mt-6 h-72 w-full sm:h-96" />
          </div>
        )}
      </Card>
      <RecommendationCard ticker={ticker} />
      <FilingsSection ticker={ticker} />
    </div>
  )
}
