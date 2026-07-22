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
      <label className="block text-sm font-bold text-ink">
        {label}
        {required && <span className="ml-1.5 rounded-full bg-brand-pink-soft px-2 py-0.5 text-xs font-bold text-brand-pink">必須</span>}
      </label>
      {hint && <p className="text-xs text-ink-soft">{hint}</p>}
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
  'w-full rounded-2xl border border-line-strong bg-white px-3.5 py-2.5 text-sm transition-colors placeholder:text-ink-faint focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15'

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
            className={`flex h-13 flex-1 flex-col items-center justify-center rounded-2xl border text-xs transition-all ${
              value === n
                ? 'border-brand-leaf bg-brand-leaf-soft font-bold text-ink ring-4 ring-brand-leaf/15 scale-[1.04]'
                : 'border-line bg-white text-ink-soft hover:bg-paper hover:border-line-strong'
            }`}
          >
            <span aria-hidden className="text-base leading-none">{emojis[n]}</span>
            <span>{n}</span>
          </button>
        ))}
      </div>
      <div className="mt-1.5 flex justify-between text-xs text-ink-faint">
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
          className={`flex-1 rounded-2xl border px-2 py-2.5 text-sm transition-all ${
            value === opt.value
              ? 'border-brand-leaf bg-brand-leaf-soft font-bold text-ink ring-4 ring-brand-leaf/15'
              : 'border-line bg-white text-ink-soft hover:bg-paper hover:border-line-strong'
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
      className={`rounded-2xl bg-brand-leaf px-5 py-2.5 text-sm font-bold text-white shadow-[0_4px_14px_-4px_rgb(106_175_92/0.55)] transition-all hover:brightness-105 hover:shadow-[0_6px_18px_-4px_rgb(106_175_92/0.65)] active:scale-[0.98] disabled:opacity-50 disabled:shadow-none ${props.className ?? ''}`}
    >
      {children}
    </button>
  )
}

export function SecondaryButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`rounded-2xl border border-line-strong bg-white px-5 py-2.5 text-sm font-bold text-ink-soft transition-colors hover:bg-paper active:scale-[0.98] disabled:opacity-50 ${props.className ?? ''}`}
    >
      {children}
    </button>
  )
}
