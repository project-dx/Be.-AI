import { useEffect, useState } from 'react'
import { errorMessage, staffReportsApi } from '../../services/api'
import { Badge, Card, EmptyState, ErrorMessage, Loading } from '../../components/ui'
import { formatDate, urgencyLabels } from '../../utils/labels'
import type { StaffReport } from '../../types'

export default function StaffReportsPanel({ userId }: { userId: number }) {
  const [reports, setReports] = useState<StaffReport[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [openId, setOpenId] = useState<number | null>(null)

  useEffect(() => {
    staffReportsApi
      .list(userId)
      .then(setReports)
      .catch((e) => setError(errorMessage(e)))
  }, [userId])

  if (error) return <ErrorMessage message={error} />
  if (!reports) return <Loading />

  if (reports.length === 0) {
    return <EmptyState message="スタッフ日報はまだ登録されていません。「スタッフ日報を書く」から登録できます" />
  }

  return (
    <div className="space-y-3">
      {reports.map((r) => {
        const urgency = urgencyLabels[r.urgency]
        return (
          <Card key={r.id} className={r.urgency === 'urgent' ? 'border-rose-300 border-2' : ''}>
            <button
              className="flex w-full items-center justify-between text-left"
              onClick={() => setOpenId(openId === r.id ? null : r.id)}
              aria-expanded={openId === r.id}
            >
              <span className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-bold text-slate-700">{formatDate(r.report_date)}</span>
                <Badge label={urgency.label} className={urgency.className} />
                <span className="text-slate-500">{r.staff_name ?? ''}</span>
                <span className="text-slate-400">{r.support_minutes != null ? `${r.support_minutes}分` : ''}</span>
              </span>
              <span aria-hidden className="text-slate-400">{openId === r.id ? '▲' : '▼'}</span>
            </button>
            {openId !== r.id && r.support_content && (
              <p className="mt-1 truncate text-sm text-slate-500">{r.support_content}</p>
            )}
            {openId === r.id && (
              <dl className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-sm">
                {(
                  [
                    ['支援内容', r.support_content],
                    ['利用者の様子', r.user_condition],
                    ['会話内容', r.conversation_summary],
                    ['良かった点', r.positive_points],
                    ['課題', r.issues],
                    ['行動変化', r.behavior_changes],
                    ['実施した支援方法', r.support_method],
                    ['利用者の反応', r.user_response],
                    ['次回確認事項', r.next_check],
                    ['自由記述', r.free_text],
                  ] as const
                )
                  .filter(([, v]) => v)
                  .map(([label, value]) => (
                    <div key={label}>
                      <dt className="text-xs font-bold text-slate-400">{label}</dt>
                      <dd className="whitespace-pre-wrap text-slate-700">{value}</dd>
                    </div>
                  ))}
              </dl>
            )}
          </Card>
        )
      })}
    </div>
  )
}
