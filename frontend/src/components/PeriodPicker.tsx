/** 期間の候補（クイック選択） */
export interface PeriodPreset {
  label: string
  days: number
}

export const SHORT_PRESETS: PeriodPreset[] = [
  { label: '1週間', days: 7 },
  { label: '2週間', days: 14 },
  { label: '1か月', days: 30 },
  { label: '3か月', days: 90 },
]

export const LONG_PRESETS: PeriodPreset[] = [
  { label: '3か月', days: 90 },
  { label: '6か月', days: 180 },
  { label: '1年', days: 365 },
]

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10)
}

export function daysAgoISO(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - (days - 1))
  return d.toISOString().slice(0, 10)
}

/**
 * カレンダーから期間（開始日・終了日）を選ぶ。
 * クイック選択ボタンでよく使う期間をすぐ指定できる。
 */
export function PeriodPicker({
  start,
  end,
  onChange,
  presets = SHORT_PRESETS,
  disabled = false,
}: {
  start: string
  end: string
  onChange: (start: string, end: string) => void
  presets?: PeriodPreset[]
  disabled?: boolean
}) {
  const inputClass =
    'rounded-xl border border-line-strong bg-white px-3 py-1.5 text-sm focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15 disabled:opacity-60'

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1.5">
        <input
          type="date"
          aria-label="開始日"
          value={start}
          max={end}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value, end)}
          className={inputClass}
        />
        <span aria-hidden className="text-ink-faint">〜</span>
        <input
          type="date"
          aria-label="終了日"
          value={end}
          min={start}
          max={todayISO()}
          disabled={disabled}
          onChange={(e) => onChange(start, e.target.value)}
          className={inputClass}
        />
      </div>
      <div className="flex flex-wrap gap-1.5">
        {presets.map((p) => (
          <button
            key={p.label}
            type="button"
            disabled={disabled}
            onClick={() => onChange(daysAgoISO(p.days), todayISO())}
            className="rounded-full border border-line-strong bg-white px-3 py-1 text-xs font-bold text-ink-soft transition-colors hover:bg-paper disabled:opacity-60"
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  )
}
