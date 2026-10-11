export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-(--grid) ${className}`} aria-hidden />
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center gap-3 text-sm text-(--text-secondary)">
      <span>
        <span className="text-(--status-critical)" aria-hidden>
          ●{' '}
        </span>
        {message}
      </span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-md border border-(--border) px-2.5 py-1 font-medium text-(--text-primary) hover:bg-(--surface-0)"
        >
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-(--text-muted)">{children}</p>
}
