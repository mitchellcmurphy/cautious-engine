import { ApiError } from '../api/client'
import { useFilings } from '../hooks/useFilings'
import { Card } from './Card'
import { FilingCard } from './FilingCard'
import { EmptyState, ErrorState, Skeleton } from './states'

export function FilingsSection({ ticker }: { ticker: string }) {
  const filings = useFilings(ticker)

  return (
    <Card title="SEC filings summary" aside={<span className="text-xs text-(--text-muted)">Latest 10-K & 10-Q</span>}>
      {filings.isPending ? (
        <div className="space-y-3" aria-busy="true">
          <p className="text-sm text-(--text-secondary)" role="status">
            Fetching and summarizing filings from SEC EDGAR — the first load for a ticker can take up to a minute.
          </p>
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      ) : filings.isError ? (
        filings.error instanceof ApiError && filings.error.code === 'no_recent_filings' ? (
          <EmptyState>{filings.error.message}</EmptyState>
        ) : (
          <ErrorState message={`Couldn't load filings: ${filings.error.message}`} onRetry={() => filings.refetch()} />
        )
      ) : (
        <div className="space-y-4">
          {filings.data.warnings.length > 0 && (
            <ul role="note" className="space-y-1 rounded-md border border-(--border) px-3 py-2 text-sm text-(--text-secondary)">
              {filings.data.warnings.map((w, i) => (
                <li key={i}>
                  <span aria-hidden style={{ color: 'var(--status-warning)' }}>
                    ⚠{' '}
                  </span>
                  {w}
                </li>
              ))}
            </ul>
          )}
          {filings.data.filings.length === 0 ? (
            <EmptyState>No recent 10-K or 10-Q filings found for {ticker}.</EmptyState>
          ) : (
            filings.data.filings.map((f) => <FilingCard key={f.meta.accession_number} filing={f} />)
          )}
        </div>
      )}
    </Card>
  )
}
