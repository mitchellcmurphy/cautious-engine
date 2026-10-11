import {
  AreaSeries,
  ColorType,
  createChart,
  CrosshairMode,
  TickMarkType,
  type IChartApi,
  type ISeriesApi,
  type Time,
  type UTCTimestamp,
} from 'lightweight-charts'
import { useEffect, useRef, useState } from 'react'
import type { PricePoint } from '../api/types'
import { toBarTime } from '../lib/chartMath'
import { formatMarketDateTime, formatMarketTime, formatMarketTimeWithSeconds, formatMoney } from '../lib/format'

const timeToDate = (t: Time) => new Date((t as number) * 1000)

function readTheme(el: HTMLElement) {
  const css = getComputedStyle(el)
  const v = (name: string) => css.getPropertyValue(name).trim()
  return {
    surface: v('--surface-1'),
    grid: v('--grid'),
    border: v('--border'),
    text: v('--text-secondary'),
    series: v('--series-1'),
  }
}

/** #rrggbb → rgba() so the area fill can be a ~10% wash of the series hue. */
function withAlpha(hex: string, alpha: number) {
  const n = parseInt(hex.replace('#', ''), 16)
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`
}

function applyTheme(el: HTMLElement, chart: IChartApi, series: ISeriesApi<'Area'>) {
  const t = readTheme(el)
  chart.applyOptions({
    layout: { background: { type: ColorType.Solid, color: t.surface }, textColor: t.text },
    grid: { vertLines: { visible: false }, horzLines: { color: t.grid } },
    rightPriceScale: { borderColor: t.border },
    timeScale: { borderColor: t.border },
  })
  series.applyOptions({ lineColor: t.series, topColor: withAlpha(t.series, 0.12), bottomColor: withAlpha(t.series, 0.01) })
}

const toSeriesPoint = (p: PricePoint) => ({ time: toBarTime(p.t, 1) as UTCTimestamp, value: p.price })

export function PriceChart({
  ticker,
  points,
  currency,
  marketOpen,
}: {
  ticker: string
  points: PricePoint[]
  currency: string
  marketOpen: boolean
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null)
  const renderedRef = useRef<PricePoint[]>([])

  // Create once; follow light/dark changes.
  useEffect(() => {
    const el = containerRef.current!
    const chart = createChart(el, {
      autoSize: true,
      layout: { fontFamily: getComputedStyle(document.body).fontFamily, fontSize: 12 },
      crosshair: { mode: CrosshairMode.Magnet },
      localization: {
        timeFormatter: (t: Time) => formatMarketDateTime(timeToDate(t)),
        priceFormatter: (n: number) => formatMoney(n, currency),
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
        // Seconds only matter for the first few minutes of collected prices.
        tickMarkFormatter: (t: Time, type: TickMarkType) =>
          type === TickMarkType.TimeWithSeconds
            ? formatMarketTimeWithSeconds(timeToDate(t))
            : formatMarketTime(timeToDate(t)),
      },
      handleScroll: false,
      handleScale: false,
    })
    const series = chart.addSeries(AreaSeries, {
      lineWidth: 2,
      priceLineVisible: false,
      crosshairMarkerRadius: 4,
    })
    chartRef.current = chart
    seriesRef.current = series
    applyTheme(el, chart, series)

    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const onScheme = () => applyTheme(el, chart, series)
    media.addEventListener('change', onScheme)

    // Always show the whole series, whatever the container width.
    const resize = new ResizeObserver(() =>
      requestAnimationFrame(() => chartRef.current === chart && chart.timeScale().fitContent()),
    )
    resize.observe(el)

    return () => {
      resize.disconnect()
      media.removeEventListener('change', onScheme)
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
      renderedRef.current = []
    }
  }, [currency])

  // Append the newest point when the series grew by one; otherwise reset the data.
  useEffect(() => {
    const series = seriesRef.current
    if (!series) return
    const prev = renderedRef.current
    if (points.length < 2) {
      series.setData([]) // a lone point renders as a stray half-line
    } else if (prev.length >= 2 && points.length === prev.length + 1 && points.at(-2) === prev.at(-1)) {
      series.update(toSeriesPoint(points.at(-1)!))
    } else {
      series.setData(points.map(toSeriesPoint))
    }
    renderedRef.current = points
    chartRef.current?.timeScale().fitContent()
  }, [points])

  return (
    <figure className="m-0">
      <div className="relative">
        <div
          ref={containerRef}
          className="h-72 w-full sm:h-96"
          role="img"
          aria-label={`Live price chart for ${ticker} since this page was opened`}
        />
        {points.length < 2 && (
          <p className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center px-6 text-center text-sm text-(--text-muted)">
            {marketOpen
              ? 'Collecting prices — the chart fills in as new quotes arrive.'
              : 'The market is closed. The chart fills in with live prices during trading hours.'}
          </p>
        )}
      </div>
      <DataTable points={points} currency={currency} />
    </figure>
  )
}

/** Accessible fallback: the same points as a table, rendered only when expanded. */
function DataTable({ points, currency }: { points: PricePoint[]; currency: string }) {
  const [open, setOpen] = useState(false)
  return (
    <details className="mt-3 text-sm" onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary className="cursor-pointer text-(--text-secondary)">View data table</summary>
      {open && (
        <div className="mt-2 max-h-64 overflow-y-auto rounded-md border border-(--border)">
          <table className="w-full tabular-nums">
            <thead className="sticky top-0 bg-(--surface-1) text-left text-(--text-muted)">
              <tr>
                <th className="px-3 py-1.5 font-medium">Time (ET)</th>
                <th className="px-3 py-1.5 text-right font-medium">Price</th>
              </tr>
            </thead>
            <tbody>
              {points.map((p) => (
                <tr key={p.t} className="border-t border-(--grid)">
                  <td className="px-3 py-1">{formatMarketTimeWithSeconds(new Date(p.t))}</td>
                  <td className="px-3 py-1 text-right">{formatMoney(p.price, currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  )
}
