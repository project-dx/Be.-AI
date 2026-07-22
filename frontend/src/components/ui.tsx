import type { ReactNode } from 'react'

export function Card({ title, children, className = '', accent }: {
  title?: ReactNode
  children: ReactNode
  className?: string
  accent?: string
}) {
  return (
    <section
      className={`rounded-3xl bg-white border border-line p-5 sm:p-6 shadow-card transition-shadow hover:shadow-card-hover ${className}`}
    >
      {title != null && (
        <h2 className={`mb-4 text-sm font-bold tracking-wide ${accent ?? 'text-ink-soft'}`}>{title}</h2>
      )}
      {children}
    </section>
  )
}

export function EmptyState({ message = 'まだデータがありません' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-line-strong bg-paper py-10 px-4 text-center">
      <span aria-hidden className="text-3xl">🌱</span>
      <p className="mt-3 text-sm text-ink-soft">{message}</p>
    </div>
  )
}

export function Badge({ label, className }: { label: string; className: string }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ${className}`}>
      {label}
    </span>
  )
}

export function Loading({ label = '読み込み中…' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-14 text-ink-soft" role="status">
      <span className="flex gap-1.5" aria-hidden>
        <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-brand-pink [animation-delay:-0.3s]" />
        <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-brand-sun [animation-delay:-0.15s]" />
        <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-brand-sea" />
      </span>
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorMessage({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
      {message}
    </div>
  )
}

export function AiDisclaimer() {
  return (
    <p className="rounded-2xl border border-brand-sea/25 bg-brand-sea-soft px-4 py-2.5 text-xs leading-relaxed text-ink-soft">
      ℹ️ AIによる分析結果は医療診断ではなく、支援判断を補助する参考情報です。スタッフの判断を代替するものではありません。
    </p>
  )
}

const scoreColors: Record<string, { chip: string; text: string; ring: string }> = {
  emerald: { chip: 'bg-brand-leaf-soft', text: 'text-brand-leaf', ring: 'ring-brand-leaf/15' },
  sky: { chip: 'bg-brand-sea-soft', text: 'text-brand-sea', ring: 'ring-brand-sea/15' },
  amber: { chip: 'bg-brand-sun-soft', text: 'text-brand-sun', ring: 'ring-brand-sun/20' },
  pink: { chip: 'bg-brand-pink-soft', text: 'text-brand-pink', ring: 'ring-brand-pink/15' },
  violet: { chip: 'bg-brand-plum-soft', text: 'text-brand-plum', ring: 'ring-brand-plum/15' },
  rose: { chip: 'bg-rose-50', text: 'text-rose-600', ring: 'ring-rose-200/60' },
}

export function ScoreCard({ title, value, unit = '点', icon, color = 'emerald', note }: {
  title: string
  value: number | string | null | undefined
  unit?: string
  icon: string
  color?: keyof typeof scoreColors
  note?: string
}) {
  const c = scoreColors[color] ?? scoreColors.emerald
  return (
    <div className="flex items-center gap-3.5 rounded-3xl bg-white border border-line p-4 sm:p-5 shadow-card">
      <div
        className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-2xl ring-4 ${c.chip} ${c.ring}`}
        aria-hidden
      >
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs font-bold text-ink-faint tracking-wide">{title}</p>
        {value == null ? (
          <p className="text-sm text-ink-faint mt-0.5">データなし</p>
        ) : (
          <p className={`font-display text-[1.7rem] font-black leading-tight ${c.text}`}>
            {value}
            <span className="ml-1 text-xs font-bold text-ink-faint">{unit}</span>
          </p>
        )}
        {note && <p className="text-xs text-ink-faint truncate">{note}</p>}
      </div>
    </div>
  )
}

export function ProgressBar({ value, label }: { value: number; label?: string }) {
  return (
    <div>
      {label && (
        <div className="mb-1.5 flex justify-between text-xs text-ink-soft">
          <span>{label}</span>
          <span className="font-bold">{value}%</span>
        </div>
      )}
      <div className="h-3 w-full overflow-hidden rounded-full bg-paper-deep" role="progressbar"
        aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-leaf to-brand-sea transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  )
}
