export const MARKET_TZ = 'America/New_York'

const moneyFormatters = new Map<string, Intl.NumberFormat>()
const signedPct = new Intl.NumberFormat('en-US', {
  style: 'percent',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: 'exceptZero',
})
const signedNum = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: 'exceptZero',
})
const marketTime = new Intl.DateTimeFormat('en-US', { timeZone: MARKET_TZ, hour: 'numeric', minute: '2-digit' })
const marketTimeSec = new Intl.DateTimeFormat('en-US', {
  timeZone: MARKET_TZ,
  hour: 'numeric',
  minute: '2-digit',
  second: '2-digit',
})
const marketDateTime = new Intl.DateTimeFormat('en-US', {
  timeZone: MARKET_TZ,
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  second: '2-digit',
  timeZoneName: 'short',
})
// Date-only strings ("2026-02-14") parse as UTC midnight; format in UTC so the day doesn't shift.
const calendarDate = new Intl.DateTimeFormat('en-US', { timeZone: 'UTC', month: 'short', day: 'numeric', year: 'numeric' })
const localDateTime = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' })

export function formatMoney(n: number, currency = 'USD') {
  let f = moneyFormatters.get(currency)
  if (!f) {
    f = new Intl.NumberFormat('en-US', { style: 'currency', currency })
    moneyFormatters.set(currency, f)
  }
  return f.format(n)
}

const shares = new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 })
export const formatShares = (n: number) => shares.format(n)

export function formatSignedMoney(n: number, currency = 'USD') {
  const abs = formatMoney(Math.abs(n), currency)
  return n > 0 ? `+${abs}` : n < 0 ? `-${abs}` : abs
}

/** Takes percent units (1.23 → "+1.23%"). */
export const formatSignedPct = (pct: number) => signedPct.format(pct / 100)
export const formatSigned = (n: number) => signedNum.format(n)
export const formatMarketTime = (d: Date) => marketTime.format(d)
export const formatMarketTimeWithSeconds = (d: Date) => marketTimeSec.format(d)
export const formatMarketDateTime = (d: Date) => marketDateTime.format(d)
export const formatCalendarDate = (isoDate: string) => calendarDate.format(new Date(isoDate))
export const formatLocalDateTime = (iso: string) => localDateTime.format(new Date(iso))

/** Normalizes user input to a plausible ticker (e.g. "brk.b" → "BRK.B"), or null. */
export function normalizeSymbol(input: string): string | null {
  const s = input.trim().toUpperCase()
  return /^[A-Z][A-Z0-9.-]{0,9}$/.test(s) ? s : null
}
