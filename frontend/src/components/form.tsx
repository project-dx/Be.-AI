import type { ReactNode } from 'react'

export function Field({ label, required, error, children, hint }: {
  label: string
  required?: boolean
  error?: string
  hint?: string
  children: ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-bold text-slate-700">
        {label}
        {required && <span className="ml-1 rounded bg-rose-100 px-1.5 py-0.5 text-xs text-rose-700">必須</span>}
      </label>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      {children}
      {error && (
        <p role="alert" className="text-xs font-bold text-rose-600">
          {error}
        </p>
      )}
    </div>
  )
}

export const inputClass =
  'w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-200'

const scaleEmojis: Record<number, string> = { 1: '😞', 2: '😕', 3: '😐', 4: '🙂', 5: '😄' }
const scaleEmojisReverse: Record<number, string> = { 1: '😄', 2: '🙂', 3: '😐', 4: '😣', 5: '😫' }

/** 1〜5の評価入力（アクセシブルなラジオグループ） */
export function ScaleInput({ value, onChange, name, reverse = false, lowLabel, highLabel }: {
  value: number | null
  onChange: (v: number) => void
  name: string
  reverse?: boolean
  lowLabel: string
  highLabel: string
}) {
  const emojis = reverse ? scaleEmojisReverse : scaleEmojis
  return (
    <div>
      <div role="radiogroup" aria-label={name} className="flex gap-2">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            aria-label={`${n}`}
            onClick={() => onChange(n)}
            className={`flex h-12 flex-1 flex-col items-center justify-center rounded-xl border text-xs transition-colors ${
              value === n
                ? 'border-emerald-500 bg-emerald-50 font-bold text-emerald-800 ring-2 ring-emerald-200'
                : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'
            }`}
          >
            <span aria-hidden className="text-base leading-none">{emojis[n]}</span>
            <span>{n}</span>
          </button>
        ))}
      </div>
      <div className="mt-1 flex justify-between text-xs text-slate-400">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  )
}

/** 食事状況の選択 */
export function MealInput({ value, onChange }: {
  value: string | null
  onChange: (v: 'eaten' | 'partial' | 'skipped') => void
}) {
  const options = [
    { value: 'eaten', label: '食べた' },
    { value: 'partial', label: '少し食べた' },
    { value: 'skipped', label: '食べていない' },
  ] as const
  return (
    <div className="flex gap-2" role="radiogroup">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          onClick={() => onChange(opt.value)}
          className={`flex-1 rounded-xl border px-2 py-2.5 text-sm transition-colors ${
            value === opt.value
              ? 'border-emerald-500 bg-emerald-50 font-bold text-emerald-800'
              : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

export function PrimaryButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-50 ${props.className ?? ''}`}
    >
      {children}
    </button>
  )
}

export function SecondaryButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50 ${props.className ?? ''}`}
    >
      {children}
    </button>
  )
}
