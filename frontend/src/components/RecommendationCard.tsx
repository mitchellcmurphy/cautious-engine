import { ApiError } from '../api/client'
import type { Recommendation } from '../api/types'
import { useRecommendation } from '../hooks/useRecommendation'
import {
  formatCalendarDate,
  formatLocalDateTime,
  formatMoney,
  formatShares,
  formatSignedMoney,
  formatSignedPct,
} from '../lib/format'
import { CONFIDENCE_LABEL } from '../lib/labels'
import { Card } from './Card'
import { Chip, GainLoss, Glyph } from './Chip'
import { ErrorState, Skeleton } from './states'

const ACTION: Record<Recommendation['action'], { label: string; icon: string; color: string }> = {
  buy: { label: 'Buy', icon: '▲', color: 'var(--status-good)' },
  sell: { label: 'Sell', icon: '▼', color: 'var(--status-critical)' },
  hold: { label: 'Hold', icon: '■', color: 'var(--accent)' },
  pass: { label: 'Pass', icon: '–', color: 'var(--text-muted)' },
}

const PERIODS = [
  ['1M', 'return_1m'],
  ['3M', 'return_3m'],
  ['6M', 'return_6m'],
  ['1Y', 'return_1y'],
] as const

function Tile({ label, children, sub }: { label: string; children: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="rounded-md bg-(--surface-0) px-3 py-2">
      <dt className="text-xs text-(--text-secondary)">{label}</dt>
      <dd className="m-0 text-lg font-semibold tabular-nums">{children}</dd>
      {sub && <dd className="m-0 text-xs text-(--text-muted)">{sub}</dd>}
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="mb-2 text-sm font-semibold">{children}</h3>
}

function RecommendationBody({ rec }: { rec: Recommendation }) {
  const action = ACTION[rec.action]
  const pos = rec.position

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <p className="inline-flex items-center gap-2 rounded-lg border border-(--border) px-3 py-1.5 text-2xl font-semibold">
          <Glyph icon={action.icon} color={action.color} />
          {action.label}
        </p>
        <Chip>{rec.owned ? 'Held in portfolio' : 'Not currently held'}</Chip>
        <Chip>{CONFIDENCE_LABEL[rec.confidence]}</Chip>
      </div>

      <p className="mt-4 leading-relaxed">{rec.rationale}</p>

      {rec.key_factors.length > 0 && (
        <section className="mt-5">
          <SectionTitle>Key factors</SectionTitle>
          <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed">
            {rec.key_factors.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-5">
        <SectionTitle>Performance</SectionTitle>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {PERIODS.map(([label, key]) => {
            const v = rec.performance[key]
            return (
              <Tile key={key} label={`${label} return`}>
                {v === null ? (
                  <span className="text-(--text-muted)">—</span>
                ) : (
                  <GainLoss value={v}>{formatSignedPct(v)}</GainLoss>
                )}
              </Tile>
            )
          })}
        </dl>
        <p className="mt-1 text-xs text-(--text-muted)">As of {formatCalendarDate(rec.performance.as_of)}</p>
      </section>

      {pos && (
        <section className="mt-5">
          <SectionTitle>Firm position</SectionTitle>
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Tile label="Shares">{formatShares(pos.total_shares)}</Tile>
            <Tile label="Avg cost">{formatMoney(pos.avg_price_per_share)}</Tile>
            <Tile label="Market value">{formatMoney(pos.market_value)}</Tile>
            <Tile label="Unrealized G/L" sub={formatSignedPct(pos.unrealized_gain_loss_pct)}>
              <GainLoss value={pos.unrealized_gain_loss}>{formatSignedMoney(pos.unrealized_gain_loss)}</GainLoss>
            </Tile>
          </dl>
        </section>
      )}

      {rec.based_on_filings.length > 0 && (
        <section className="mt-5">
          <SectionTitle>Based on filings</SectionTitle>
          <ul className="space-y-1 text-sm">
            {rec.based_on_filings.map((f) => (
              <li key={f.accession_number}>
                <a
                  href={f.primary_document_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-(--accent) underline-offset-2 hover:underline"
                >
                  {f.form_type} filed {formatCalendarDate(f.filing_date)} ↗
                </a>
                {f.period_of_report && (
                  <span className="text-(--text-muted)"> · period ending {formatCalendarDate(f.period_of_report)}</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer className="mt-5 text-xs text-(--text-muted)">
        AI-generated recommendation · {formatLocalDateTime(rec.generated_at)} · Review before acting on it.
      </footer>
    </div>
  )
}

export function RecommendationCard({ ticker }: { ticker: string }) {
  const rec = useRecommendation(ticker)

  return (
    <Card title="Recommendation">
      {rec.isPending ? (
        <div className="space-y-3" aria-busy="true">
          <p className="text-sm text-(--text-secondary)" role="status">
            Generating a recommendation from recent filings and performance — the first one for a ticker can take a minute or two.
          </p>
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      ) : rec.isError ? (
        <ErrorState
          message={
            rec.error instanceof ApiError && rec.error.status === 404
              ? rec.error.message
              : `Couldn't generate a recommendation: ${rec.error.message}`
          }
          onRetry={() => rec.refetch()}
        />
      ) : (
        <RecommendationBody rec={rec.data} />
      )}
    </Card>
  )
}
