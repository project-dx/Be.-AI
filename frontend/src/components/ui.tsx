import type { ReactNode } from 'react'

export function Card({ title, children, className = '', accent }: {
  title?: ReactNode
  children: ReactNode
  className?: string
  accent?: string
}) {
  return (
    <section className={`rounded-2xl bg-white border border-slate-200 p-4 sm:p-5 ${className}`}>
      {title != null && (
        <h2 className={`mb-3 text-sm font-bold ${accent ?? 'text-slate-600'}`}>{title}</h2>
      )}
      {children}
    </section>
  )
}

export function EmptyState({ message = 'まだデータがありません' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl bg-slate-50 py-8 px-4 text-center">
      <span aria-hidden className="text-2xl">🌱</span>
      <p className="mt-2 text-sm text-slate-500">{message}</p>
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
    <div className="flex items-center justify-center gap-2 py-10 text-slate-500" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" aria-hidden />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorMessage({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
      {message}
    </div>
  )
}

export function AiDisclaimer() {
  return (
    <p className="rounded-xl bg-sky-50 border border-sky-200 px-4 py-2.5 text-xs text-sky-900">
      ℹ️ AIによる分析結果は医療診断ではなく、支援判断を補助する参考情報です。スタッフの判断を代替するものではありません。
    </p>
  )
}

const scoreColors: Record<string, { bg: string; text: string }> = {
  emerald: { bg: 'bg-emerald-100', text: 'text-emerald-700' },
  sky: { bg: 'bg-sky-100', text: 'text-sky-700' },
  amber: { bg: 'bg-amber-100', text: 'text-amber-700' },
  pink: { bg: 'bg-pink-100', text: 'text-pink-700' },
  violet: { bg: 'bg-violet-100', text: 'text-violet-700' },
  rose: { bg: 'bg-rose-100', text: 'text-rose-700' },
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
    <div className="flex items-center gap-3 rounded-2xl bg-white border border-slate-200 p-4">
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-xl ${c.bg}`} aria-hidden>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs font-bold text-slate-500">{title}</p>
        {value == null ? (
          <p className="text-sm text-slate-400 mt-0.5">データなし</p>
        ) : (
          <p className={`text-2xl font-bold leading-tight ${c.text}`}>
            {value}
            <span className="ml-0.5 text-xs font-normal text-slate-500">{unit}</span>
          </p>
        )}
        {note && <p className="text-xs text-slate-400 truncate">{note}</p>}
      </div>
    </div>
  )
}

export function ProgressBar({ value, label }: { value: number; label?: string }) {
  return (
    <div>
      {label && (
        <div className="mb-1 flex justify-between text-xs text-slate-500">
          <span>{label}</span>
          <span>{value}%</span>
        </div>
      )}
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100" role="progressbar"
        aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
    </div>
  )
}
