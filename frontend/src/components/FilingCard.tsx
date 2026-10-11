import type { FilingSummary } from '../api/types'
import { formatCalendarDate, formatLocalDateTime } from '../lib/format'
import { CONFIDENCE_LABEL } from '../lib/labels'
import { Chip } from './Chip'

const SENTIMENT: Record<FilingSummary['sentiment'], { label: string; icon: string; color: string }> = {
  positive: { label: 'Positive', icon: '▲', color: 'var(--status-good)' },
  negative: { label: 'Negative', icon: '▼', color: 'var(--status-critical)' },
  mixed: { label: 'Mixed', icon: '◆', color: 'var(--status-warning)' },
  neutral: { label: 'Neutral', icon: '●', color: 'var(--text-muted)' },
}

export function FilingCard({ filing }: { filing: FilingSummary }) {
  const { meta } = filing
  const sentiment = SENTIMENT[filing.sentiment]

  return (
    <article className="rounded-lg border border-(--border) p-4 sm:p-5">
      <header className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div>
          <h3 className="text-base font-semibold">
            {meta.form_type === '10-K' ? 'Annual report' : 'Quarterly report'}{' '}
            <span className="text-(--text-secondary)">· {meta.form_type}</span>
          </h3>
          <p className="text-sm text-(--text-muted)">
            Filed {formatCalendarDate(meta.filing_date)}
            {meta.period_of_report && <> · Period ending {formatCalendarDate(meta.period_of_report)}</>}
          </p>
        </div>
        <a
          href={meta.primary_document_url}
          target="_blank"
          rel="noreferrer"
          className="text-sm font-medium text-(--accent) underline-offset-2 hover:underline"
        >
          View on EDGAR ↗
        </a>
      </header>

      <div className="mt-3 flex flex-wrap gap-2">
        <Chip>
          <span aria-hidden style={{ color: sentiment.color }}>
            {sentiment.icon}
          </span>
          {sentiment.label} sentiment
        </Chip>
        <Chip>{CONFIDENCE_LABEL[filing.confidence]}</Chip>
      </div>

      <p className="mt-4 text-base font-medium leading-relaxed">{filing.tldr}</p>
      <p className="mt-2 text-sm leading-relaxed text-(--text-secondary)">{filing.overview}</p>

      {filing.financial_highlights.length > 0 && (
        <section className="mt-5">
          <h4 className="mb-2 text-sm font-semibold">Financial highlights</h4>
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filing.financial_highlights.map((h, i) => (
              <div key={`${h.label}-${i}`} className="rounded-md bg-(--surface-0) px-3 py-2">
                <dt className="text-xs text-(--text-secondary)">{h.label}</dt>
                <dd className="m-0 text-lg font-semibold tabular-nums">{h.value}</dd>
                {h.period && <dd className="m-0 text-xs text-(--text-muted)">{h.period}</dd>}
              </div>
            ))}
          </dl>
        </section>
      )}

      {filing.notable_risks_or_changes.length > 0 && (
        <section className="mt-5">
          <h4 className="mb-2 text-sm font-semibold">Notable risks & changes</h4>
          <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed">
            {filing.notable_risks_or_changes.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </section>
      )}

      <footer className="mt-5 text-xs text-(--text-muted)">
        AI-generated summary · {formatLocalDateTime(filing.generated_at)} · Accession {meta.accession_number}
      </footer>
    </article>
  )
}
