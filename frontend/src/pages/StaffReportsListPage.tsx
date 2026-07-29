import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage, staffReportsApi, usersApi } from '../services/api'
import { Badge, Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { formatDate, urgencyLabels } from '../utils/labels'
import type { StaffReport, Urgency } from '../types'

const URGENCY_FILTERS: { key: '' | Urgency; label: string }[] = [
  { key: '', label: 'すべて' },
  { key: 'urgent', label: '至急' },
  { key: 'check', label: '要確認' },
  { key: 'caution', label: '注意' },
  { key: 'normal', label: '通常' },
]

const DETAIL_FIELDS: { key: keyof StaffReport; label: string }[] = [
  { key: 'user_condition', label: '利用者の様子' },
  { key: 'conversation_summary', label: '会話の内容' },
  { key: 'positive_points', label: '良かった点' },
  { key: 'issues', label: '課題' },
  { key: 'behavior_changes', label: '行動変化' },
  { key: 'support_method', label: '支援方法' },
  { key: 'user_response', label: '利用者の反応' },
  { key: 'next_check', label: '次回の確認事項' },
]

/** 全利用者のスタッフ日報（支援記録）を横断して見る画面 */
export default function StaffReportsListPage() {
  const [reports, setReports] = useState<StaffReport[]>([])
  const [members, setMembers] = useState<{ id: number; name: string }[]>([])
  const [urgency, setUrgency] = useState<'' | Urgency>('')
  const [userId, setUserId] = useState<number | ''>('')
  const [openId, setOpenId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    staffReportsApi
      .listAll({
        urgency: urgency || undefined,
        user_id: userId === '' ? undefined : Number(userId),
      })
      .then(setReports)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false))
  }, [urgency, userId])

  useEffect(load, [load])

  useEffect(() => {
    usersApi
      .list()
      .then((list) =>
        setMembers(
          list
            .filter((u) => u.role === 'user' && u.is_active)
            .map((u) => ({ id: u.id, name: u.profile?.display_name ?? u.email })),
        ),
      )
      .catch(() => setMembers([]))
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-ink">🖊️ スタッフ日報（支援記録）</h1>
        <span className="text-xs text-ink-faint">{reports.length}件</span>
      </div>

      <ErrorMessage message={error} />

      {/* 絞り込み */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-wrap gap-1.5">
            {URGENCY_FILTERS.map((f) => (
              <button
                key={f.key || 'all'}
                onClick={() => setUrgency(f.key)}
                aria-pressed={urgency === f.key}
                className={`rounded-full px-3.5 py-1.5 text-xs font-bold transition-colors ${
                  urgency === f.key
                    ? 'bg-brand-leaf text-white'
                    : 'border border-line-strong bg-white text-ink-soft hover:bg-paper'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
          <select
            aria-label="利用者で絞り込む"
            value={userId}
            onChange={(e) => setUserId(e.target.value === '' ? '' : Number(e.target.value))}
            className="rounded-xl border border-line-strong bg-white px-3 py-1.5 text-sm focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15"
          >
            <option value="">すべての利用者</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
      </Card>

      {loading ? (
        <Card><Loading /></Card>
      ) : reports.length === 0 ? (
        <Card>
          <EmptyState message="条件に合う支援記録がありません。利用者詳細から「スタッフ日報を書く」で作成できます" />
        </Card>
      ) : (
        reports.map((r) => {
          const urgencyStyle = urgencyLabels[r.urgency]
          const isOpen = openId === r.id
          return (
            <Card key={r.id} className={r.urgency === 'urgent' ? 'border-2 border-rose-300' : ''}>
              <button
                onClick={() => setOpenId(isOpen ? null : r.id)}
                aria-expanded={isOpen}
                className="flex w-full flex-wrap items-center gap-x-3 gap-y-1.5 text-left"
              >
                <Badge label={urgencyStyle.label} className={urgencyStyle.className} />
                <Link
                  to={`/users/${r.user_id}?tab=staff-reports`}
                  onClick={(e) => e.stopPropagation()}
                  className="font-bold text-ink underline decoration-line-strong underline-offset-2 hover:decoration-brand-leaf"
                >
                  {r.user_name ?? `利用者#${r.user_id}`}
                </Link>
                <span className="text-sm text-ink-soft">{formatDate(r.report_date)}</span>
                {r.staff_name && <span className="text-xs text-ink-faint">記録: {r.staff_name}</span>}
                {r.support_minutes != null && (
                  <span className="text-xs text-ink-faint">{r.support_minutes}分</span>
                )}
                <span aria-hidden className="ml-auto text-ink-faint">{isOpen ? '▲' : '▼'}</span>
              </button>

              {r.support_content && (
                <p className="mt-2 text-sm leading-relaxed text-ink">{r.support_content}</p>
              )}

              {isOpen && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 border-t border-line pt-3 text-sm">
                  {DETAIL_FIELDS.map((f) => {
                    const value = r[f.key] as string | null
                    if (!value) return null
                    return (
                      <p key={String(f.key)}>
                        <span className="block text-xs font-bold text-ink-faint">{f.label}</span>
                        {value}
                      </p>
                    )
                  })}
                  {r.free_text && (
                    <p className="sm:col-span-2">
                      <span className="block text-xs font-bold text-ink-faint">自由記述</span>
                      {r.free_text}
                    </p>
                  )}
                </div>
              )}
            </Card>
          )
        })
      )}
    </div>
  )
}
