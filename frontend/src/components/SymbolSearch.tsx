import { useState, type FormEvent } from 'react'
import { normalizeSymbol } from '../lib/format'

export function SymbolSearch({ initial, onSubmit }: { initial: string; onSubmit: (symbol: string) => void }) {
  const [value, setValue] = useState(initial)
  const [invalid, setInvalid] = useState(false)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const symbol = normalizeSymbol(value)
    setInvalid(!symbol)
    if (symbol) {
      setValue(symbol)
      onSubmit(symbol)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-sm gap-2" role="search">
      <label htmlFor="symbol" className="sr-only">
        Stock symbol
      </label>
      <input
        id="symbol"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Symbol, e.g. AAPL"
        autoComplete="off"
        spellCheck={false}
        aria-invalid={invalid}
        aria-describedby={invalid ? 'symbol-error' : undefined}
        className="min-w-0 flex-1 rounded-lg border border-(--border) bg-(--surface-1) px-3 py-2 uppercase placeholder:normal-case placeholder:text-(--text-muted) focus:outline-2 focus:outline-(--accent)"
      />
      <button
        type="submit"
        className="rounded-lg bg-(--accent) px-4 py-2 font-medium text-white hover:opacity-90 focus:outline-2 focus:outline-offset-2 focus:outline-(--accent)"
      >
        Load
      </button>
      {invalid && (
        <span id="symbol-error" className="sr-only">
          Enter a valid ticker symbol
        </span>
      )}
    </form>
  )
}
