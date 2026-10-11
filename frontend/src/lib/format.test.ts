import { describe, expect, it } from 'vitest'
import { toBarTime } from './chartMath'
import { formatCalendarDate, formatSignedPct, normalizeSymbol } from './format'

describe('normalizeSymbol', () => {
  it('uppercases and trims', () => expect(normalizeSymbol('  aapl ')).toBe('AAPL'))
  it('allows class shares', () => expect(normalizeSymbol('brk.b')).toBe('BRK.B'))
  it('rejects junk', () => {
    expect(normalizeSymbol('')).toBeNull()
    expect(normalizeSymbol('1ABC')).toBeNull()
    expect(normalizeSymbol('AA PL')).toBeNull()
  })
})

describe('formatting', () => {
  it('treats change_percent as percent units', () => expect(formatSignedPct(1.234)).toBe('+1.23%'))
  it('does not shift date-only strings across time zones', () =>
    expect(formatCalendarDate('2026-02-14')).toBe('Feb 14, 2026'))
})

describe('toBarTime', () => {
  it('floors to the interval in epoch seconds', () => {
    expect(toBarTime('2026-10-09T14:31:42Z')).toBe(Date.UTC(2026, 9, 9, 14, 31) / 1000)
    expect(toBarTime('2026-10-09T14:31:42.900Z', 1)).toBe(Date.UTC(2026, 9, 9, 14, 31, 42) / 1000)
  })
})
