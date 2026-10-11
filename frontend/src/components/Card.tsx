import type { ReactNode } from 'react'

export function Card({ title, aside, children }: { title?: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-(--border) bg-(--surface-1) p-4 sm:p-6">
      {title && (
        <div className="mb-4 flex items-baseline justify-between gap-4">
          <h2 className="text-base font-semibold">{title}</h2>
          {aside}
        </div>
      )}
      {children}
    </section>
  )
}
