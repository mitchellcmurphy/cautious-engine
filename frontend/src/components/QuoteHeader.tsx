import type { Quote } from '../api/types'
import { useNow } from '../hooks/useNow'
import { formatMarketDateTime, formatMoney, formatSigned, formatSignedPct } from '../lib/format'

const STALE_AFTER_MS = 5000

type Tone = 'good' | 'warning' | 'muted'
type Status = { label: string; tone: Tone }

const MARKET_STATE_LABELS: Record<string, string> = {
  PRE: 'Pre-market',
  PREPRE: 'Market closed',
  POST: 'After hours',
  POSTPOST: 'Market closed',
  CLOSED: 'Market closed',
}

function quoteStatus(quote: Quote, lastSuccessAt: number, failing: boolean, now: number): Status {
  if (failing) return { label: 'Reconnecting', tone: 'warning' }
  if (quote.market_state !== 'REGULAR') {
    return { label: MARKET_STATE_LABELS[quote.market_state] ?? 'Market closed', tone: 'muted' }
  }
  return now - lastSuccessAt > STALE_AFTER_MS ? { label: 'Delayed', tone: 'warning' } : { label: 'Live', tone: 'good' }
}

const toneColor: Record<Tone, string> = {
  good: 'var(--status-good)',
  warning: 'var(--status-warning)',
  muted: 'var(--text-muted)',
}

export function QuoteHeader({
  quote,
  lastSuccessAt,
  failing,
}: {
  quote: Quote
  /** When the last poll succeeded (TanStack Query's dataUpdatedAt). */
  lastSuccessAt: number
  /** The latest poll failed but an earlier quote is still shown. */
  failing: boolean
}) {
  const now = useNow(1000)
  const status = quoteStatus(quote, lastSuccessAt, failing, now)
  const up = quote.change >= 0

  return (
    <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
      <div className="min-w-0">
        <h1 className="truncate text-sm font-semibold text-(--text-secondary)">
          {quote.company_name ? `${quote.company_name} · ` : ''}
          <span className="tracking-wide">{quote.ticker}</span>
        </h1>
        <p className="text-5xl font-semibold tabular-nums">{formatMoney(quote.price, quote.currency)}</p>
        <p className="mt-1 text-sm tabular-nums text-(--text-secondary)">
          <span aria-hidden style={{ color: up ? 'var(--status-good)' : 'var(--status-critical)' }}>
            {up ? '▲' : '▼'}{' '}
          </span>
          {formatSigned(quote.change)} ({formatSignedPct(quote.change_percent)})
          <span className="text-(--text-muted)">
            {' '}
            vs. prev close {formatMoney(quote.previous_close, quote.currency)}
          </span>
        </p>
      </div>
      <div className="text-sm sm:text-right">
        <p className="inline-flex items-center gap-1.5 font-medium" role="status">
          <span
            aria-hidden
            className={`inline-block size-2 rounded-full ${status.label === 'Live' ? 'animate-pulse' : ''}`}
            style={{ background: toneColor[status.tone] }}
          />
          {status.label}
        </p>
        <p className="text-(--text-muted)">As of {formatMarketDateTime(new Date(quote.as_of))}</p>
      </div>
    </div>
  )
}
