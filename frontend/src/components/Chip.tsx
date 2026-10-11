import type { ReactNode } from 'react'

export function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-(--border) px-2 py-0.5 text-xs font-medium text-(--text-secondary)">
      {children}
    </span>
  )
}

/** Colored glyph beside text-token label, so meaning never rides on color alone. */
export function Glyph({ icon, color }: { icon: string; color: string }) {
  return (
    <span aria-hidden style={{ color }}>
      {icon}
    </span>
  )
}

export function GainLoss({ value, children }: { value: number; children: ReactNode }) {
  return (
    <span className="tabular-nums">
      {value !== 0 && (
        <>
          <Glyph icon={value > 0 ? '▲' : '▼'} color={value > 0 ? 'var(--status-good)' : 'var(--status-critical)'} />{' '}
        </>
      )}
      {children}
    </span>
  )
}
