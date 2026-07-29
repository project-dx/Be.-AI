import { Link } from 'react-router-dom'
import { EmptyState } from './ui'
import type { DashboardWellbeingSelection } from '../types'

const ORDER_COLORS = ['bg-brand-pink', 'bg-brand-sun', 'bg-brand-sea']

function formatWhen(selectionDate: string, updatedAt: string): string {
  const d = new Date(`${selectionDate}T00:00:00`)
  const dateLabel = d.toLocaleDateString('ja-JP', { month: 'numeric', day: 'numeric', weekday: 'short' })
  const timeLabel = new Date(updatedAt).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
  return `${dateLabel} ${timeLabel}`
}

/**
 * 「誰が・いつ・どの3枚を選んだか」の一覧。
 * ダッシュボード（管理者・スタッフ）と利用者詳細で共通して使う。
 */
export function WellbeingSelectionList({
  selections,
  showUserName = true,
  emptyMessage = 'まだカードが選ばれていません',
}: {
  selections: DashboardWellbeingSelection[]
  showUserName?: boolean
  emptyMessage?: string
}) {
  if (selections.length === 0) return <EmptyState message={emptyMessage} />

  return (
    <ul className="space-y-2.5">
      {selections.map((s) => (
        <li key={s.id} className="rounded-2xl bg-paper px-4 py-3">
          <div className="flex flex-wrap items-center gap-2">
            {showUserName && (
              <Link
                to={`/users/${s.user_id}?tab=cards`}
                className="text-sm font-bold text-ink underline decoration-line-strong underline-offset-2 hover:decoration-brand-plum"
              >
                {s.user_name ?? `利用者#${s.user_id}`}
              </Link>
            )}
            <span className="text-xs text-ink-faint">{formatWhen(s.selection_date, s.updated_at)}</span>
          </div>
          <div className="mt-1.5 flex flex-wrap gap-2">
            {s.cards.map((c, i) => (
              <span
                key={c.id}
                className="inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-2.5 py-1 text-xs font-bold text-ink"
              >
                <span
                  aria-hidden
                  className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-black text-white ${ORDER_COLORS[i]}`}
                >
                  {i + 1}
                </span>
                {c.label}
              </span>
            ))}
          </div>
          {s.note && <p className="mt-1.5 text-xs text-ink-soft">「{s.note}」</p>}
        </li>
      ))}
    </ul>
  )
}
