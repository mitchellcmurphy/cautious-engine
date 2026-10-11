import { useEffect, useState } from 'react'
import { PortfolioTable } from './components/PortfolioTable'
import { StockView } from './components/StockView'
import { SymbolSearch } from './components/SymbolSearch'
import { normalizeSymbol } from './lib/format'

const symbolFromUrl = () => normalizeSymbol(new URLSearchParams(window.location.search).get('symbol') ?? '') ?? ''

export default function App() {
  const [symbol, setSymbol] = useState(symbolFromUrl)

  useEffect(() => {
    const onPop = () => setSymbol(symbolFromUrl())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const selectSymbol = (next: string) => {
    if (next === symbol) return
    const url = new URL(window.location.href)
    url.searchParams.set('symbol', next)
    window.history.pushState(null, '', url)
    setSymbol(next)
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:py-10">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <p className="text-lg font-semibold">Stock Ramp-Up</p>
        <SymbolSearch key={symbol} initial={symbol} onSubmit={selectSymbol} />
      </header>
      <main className="space-y-6">
        <PortfolioTable
          selected={symbol}
          onSelect={(ticker) => {
            selectSymbol(ticker)
            requestAnimationFrame(() =>
              document.getElementById('stock-view')?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
            )
          }}
        />
        {symbol ? (
          <div id="stock-view" className="scroll-mt-4">
            <StockView key={symbol} ticker={symbol} />
          </div>
        ) : (
          <p className="py-10 text-center text-(--text-muted)">
            Select a holding above, or search any ticker to get started.
          </p>
        )}
      </main>
    </div>
  )
}
