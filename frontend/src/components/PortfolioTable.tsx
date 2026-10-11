import type { HoldingPosition } from '../api/types'
import { usePortfolio } from '../hooks/usePortfolio'
import { formatCalendarDate, formatMoney, formatShares, formatSignedMoney, formatSignedPct } from '../lib/format'
import { Card } from './Card'
import { GainLoss } from './Chip'
import { ErrorState, Skeleton } from './states'

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-(--text-secondary)">{label}</dt>
      <dd className="m-0 text-lg font-semibold tabular-nums">{children}</dd>
    </div>
  )
}

const th = 'px-3 py-2 font-medium whitespace-nowrap'
const td = 'px-3 py-2 whitespace-nowrap tabular-nums'

function HoldingRow({ h, selected, onSelect }: { h: HoldingPosition; selected: boolean; onSelect: () => void }) {
  return (
    <tr
      onClick={onSelect}
      aria-selected={selected}
      className={`cursor-pointer border-t border-(--grid) hover:bg-(--surface-0) ${selected ? 'bg-(--surface-0)' : ''}`}
    >
      <td className={`${td} relative`}>
        {selected && <span aria-hidden className="absolute inset-y-1 left-0 w-0.5 rounded-full bg-(--accent)" />}
        {/* The button makes rows keyboard-reachable; the row click is a larger mouse target. */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onSelect()
          }}
          className="text-left font-semibold focus:outline-2 focus:outline-offset-2 focus:outline-(--accent)"
          aria-label={`Load ${h.ticker}, ${h.name}`}
        >
          {h.ticker}
        </button>
        <div className="max-w-48 truncate text-xs text-(--text-muted)">{h.name}</div>
      </td>
      <td className={`${td} hidden text-(--text-secondary) md:table-cell`}>{h.sector}</td>
      <td className={`${td} hidden text-right sm:table-cell`}>{formatShares(h.total_shares)}</td>
      <td className={`${td} hidden text-right md:table-cell`}>{formatMoney(h.avg_price_per_share)}</td>
      <td className={`${td} text-right`}>{formatMoney(h.current_price)}</td>
      <td className={`${td} hidden text-right sm:table-cell`}>{formatMoney(h.market_value)}</td>
      <td className={`${td} text-right`}>
        {/* Phones get the percent alone; the dollar figure is too wide for the column. */}
        <span className="sm:hidden">
          <GainLoss value={h.unrealized_gain_loss}>{formatSignedPct(h.unrealized_gain_loss_pct)}</GainLoss>
        </span>
        <span className="hidden sm:inline">
          <GainLoss value={h.unrealized_gain_loss}>{formatSignedMoney(h.unrealized_gain_loss)}</GainLoss>
        </span>
        <div className="hidden text-xs text-(--text-muted) sm:block">{formatSignedPct(h.unrealized_gain_loss_pct)}</div>
      </td>
    </tr>
  )
}

export function PortfolioTable({ selected, onSelect }: { selected: string; onSelect: (ticker: string) => void }) {
  const portfolio = usePortfolio()

  if (portfolio.isPending) {
    return (
      <Card title="Firm portfolio">
        <div className="space-y-3" aria-busy="true">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      </Card>
    )
  }

  if (portfolio.isError) {
    return (
      <Card title="Firm portfolio">
        <ErrorState message={`Couldn't load portfolio: ${portfolio.error.message}`} onRetry={() => portfolio.refetch()} />
      </Card>
    )
  }

  const p = portfolio.data
  const gainPct = p.total_cost_basis ? (p.total_unrealized_gain_loss / p.total_cost_basis) * 100 : 0

  return (
    <Card title={p.name} aside={<span className="text-xs text-(--text-muted)">As of {formatCalendarDate(p.as_of)}</span>}>
      <dl className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Total value">{formatMoney(p.total_market_value)}</Stat>
        <Stat label="Cash">{formatMoney(p.cash)}</Stat>
        <Stat label="Unrealized gain/loss">
          <GainLoss value={p.total_unrealized_gain_loss}>{formatSignedMoney(p.total_unrealized_gain_loss)}</GainLoss>{' '}
          <span className="text-sm font-normal text-(--text-muted)">({formatSignedPct(gainPct)})</span>
        </Stat>
      </dl>

      {p.holdings.length === 0 ? (
        <p className="text-sm text-(--text-muted)">No holdings.</p>
      ) : (
        <div className="-mx-4 overflow-x-auto sm:mx-0">
          <table className="w-full text-sm">
            <caption className="sr-only">Holdings — select one to load its quote, recommendation, and filings</caption>
            <thead className="text-left text-xs text-(--text-muted)">
              <tr>
                <th className={th}>Holding</th>
                <th className={`${th} hidden md:table-cell`}>Sector</th>
                <th className={`${th} hidden text-right sm:table-cell`}>Shares</th>
                <th className={`${th} hidden text-right md:table-cell`}>Avg cost</th>
                <th className={`${th} text-right`}>Price</th>
                <th className={`${th} hidden text-right sm:table-cell`}>Market value</th>
                <th className={`${th} text-right`}>
                  <span className="sm:hidden">G/L</span>
                  <span className="hidden sm:inline">Unrealized G/L</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {p.holdings.map((h) => (
                <HoldingRow key={h.ticker} h={h} selected={h.ticker === selected} onSelect={() => onSelect(h.ticker)} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}
