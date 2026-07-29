import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage, staffReportsApi } from '../services/api'
import { Badge, Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { SecondaryButton } from '../components/form'
import { formatDate, urgencyLabels } from '../utils/labels'
import type { StaffReport, Urgency } from '../types'

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土']

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

function currentYearMonth(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

/** 指定した月の全日付を返す（カレンダー表示用） */
function daysInMonth(yearMonth: string): Date[] {
  const [year, month] = yearMonth.split('-').map(Number)
  const last = new Date(year, month, 0).getDate()
  return Array.from({ length: last }, (_, i) => new Date(year, month - 1, i + 1))
}

function toISO(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function shiftMonth(yearMonth: string, diff: number): string {
  const [year, month] = yearMonth.split('-').map(Number)
  const d = new Date(year, month - 1 + diff, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

/** 全利用者のスタッフ日報（支援記録）を月間カレンダー／一覧で見る画面 */
export default function StaffReportsListPage() {
  const [mode, setMode] = useState<'calendar' | 'list'>('calendar')
  const [yearMonth, setYearMonth] = useState(currentYearMonth())
  const [reports, setReports] = useState<StaffReport[]>([])
  /** 記録を書いたスタッフの一覧（この画面は「誰が書いた日報か」で見る） */
  const [staffMembers, setStaffMembers] = useState<{ id: number; name: string }[]>([])
  const [urgency, setUrgency] = useState<'' | Urgency>('')
  const [staffId, setStaffId] = useState<number | ''>('')
  const [openId, setOpenId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const days = useMemo(() => daysInMonth(yearMonth), [yearMonth])

  const load = useCallback(() => {
    setLoading(true)
    const isCalendar = mode === 'calendar'
    staffReportsApi
      .listAll({
        urgency: isCalendar ? undefined : urgency || undefined,
        staff_id: staffId === '' ? undefined : Number(staffId),
        date_from: isCalendar ? `${yearMonth}-01` : undefined,
        date_to: isCalendar ? toISO(days[days.length - 1]) : undefined,
        limit: 500,
      })
      .then(setReports)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false))
  }, [mode, urgency, staffId, yearMonth, days])

  useEffect(load, [load])

  // 選択肢は「実際に記録を書いたスタッフ」から作る
  useEffect(() => {
    staffReportsApi
      .listAll({ limit: 500 })
      .then((all) => {
        const byId = new Map<number, string>()
        for (const r of all) {
          if (!byId.has(r.staff_id)) byId.set(r.staff_id, r.staff_name ?? `スタッフ#${r.staff_id}`)
        }
        const list = Array.from(byId, ([id, name]) => ({ id, name }))
        setStaffMembers(list)
        // カレンダーは1人分を見る画面なので、未選択なら先頭のスタッフを選んでおく
        setStaffId((prev) => (prev === '' && list.length > 0 ? list[0].id : prev))
      })
      .catch(() => setStaffMembers([]))
  }, [])

  /** 日付ごとの記録（1日に複数ある場合もまとめて持つ） */
  const reportsByDate = useMemo(() => {
    const map = new Map<string, StaffReport[]>()
    for (const r of reports) {
      const list = map.get(r.report_date) ?? []
      list.push(r)
      map.set(r.report_date, list)
    }
    return map
  }, [reports])

  const selectedStaffName = staffMembers.find((m) => m.id === Number(staffId))?.name

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-ink">🖊️ スタッフ日報（支援記録）</h1>
        <div className="flex gap-1.5">
          {(['calendar', 'list'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              aria-pressed={mode === m}
              className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition-colors ${
                mode === m
                  ? 'bg-brand-leaf text-white'
                  : 'border border-line-strong bg-white text-ink-soft hover:bg-paper'
              }`}
            >
              {m === 'calendar' ? '📅 カレンダー' : '📋 一覧'}
            </button>
          ))}
        </div>
      </div>

      <ErrorMessage message={error} />

      {/* 絞り込み */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-xs font-bold text-ink-soft">
            記録したスタッフ
            <select
              aria-label="記録したスタッフを選ぶ"
              value={staffId}
              onChange={(e) => setStaffId(e.target.value === '' ? '' : Number(e.target.value))}
              className="rounded-xl border border-line-strong bg-white px-3 py-1.5 text-sm font-normal focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15"
            >
              {mode === 'list' && <option value="">すべてのスタッフ</option>}
              {staffMembers.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </label>

          {mode === 'calendar' ? (
            <div className="flex items-center gap-1.5">
              <SecondaryButton onClick={() => setYearMonth(shiftMonth(yearMonth, -1))} className="px-3 py-1.5 text-xs">
                ‹ 前の月
              </SecondaryButton>
              <input
                type="month"
                aria-label="対象月"
                value={yearMonth}
                onChange={(e) => e.target.value && setYearMonth(e.target.value)}
                className="rounded-xl border border-line-strong bg-white px-3 py-1.5 text-sm focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15"
              />
              <SecondaryButton onClick={() => setYearMonth(shiftMonth(yearMonth, 1))} className="px-3 py-1.5 text-xs">
                次の月 ›
              </SecondaryButton>
            </div>
          ) : (
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
          )}
        </div>
      </Card>

      {loading ? (
        <Card><Loading /></Card>
      ) : mode === 'calendar' ? (
        /* ===== 月間カレンダー（かべなしクラウドと同じ並び） ===== */
        <Card
          title={`${yearMonth.replace('-', '年')}月 支援記録${selectedStaffName ? ` ／ ${selectedStaffName}さんが記録` : ''}`}
        >
          {staffMembers.length === 0 ? (
            <EmptyState message="支援記録がまだありません" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead>
                  <tr className="border-b-2 border-line-strong text-left text-xs text-ink-faint">
                    <th className="w-16 py-2 pr-2 font-bold">日付</th>
                    <th className="w-20 py-2 pr-2 font-bold">支援時間</th>
                    <th className="w-20 py-2 pr-2 font-bold">緊急度</th>
                    <th className="py-2 font-bold">支援記録</th>
                  </tr>
                </thead>
                <tbody>
                  {days.map((day) => {
                    const iso = toISO(day)
                    const dayReports = reportsByDate.get(iso) ?? []
                    const weekday = day.getDay()
                    const rowTone =
                      weekday === 0 ? 'bg-rose-50/60' : weekday === 6 ? 'bg-sky-50/60' : ''
                    const dateTone =
                      weekday === 0 ? 'text-rose-600' : weekday === 6 ? 'text-sky-600' : 'text-ink-soft'
                    return (
                      <tr key={iso} className={`border-b border-line align-top ${rowTone}`}>
                        <td className={`py-2.5 pr-2 text-xs font-bold ${dateTone}`}>
                          {String(day.getDate()).padStart(2, '0')}
                          <span className="block font-normal">({WEEKDAYS[weekday]})</span>
                        </td>
                        <td className="py-2.5 pr-2 text-xs text-ink-soft">
                          {dayReports.map((r) => (
                            <div key={r.id}>{r.support_minutes != null ? `${r.support_minutes}分` : '—'}</div>
                          ))}
                        </td>
                        <td className="py-2.5 pr-2">
                          {dayReports.map((r) => {
                            const u = urgencyLabels[r.urgency]
                            return (
                              <div key={r.id} className="mb-1">
                                <Badge label={u.label} className={u.className} />
                              </div>
                            )
                          })}
                        </td>
                        <td className="py-2.5">
                          {dayReports.map((r) => (
                            <div
                              key={r.id}
                              className={`mb-1.5 rounded-xl px-3 py-2 ${
                                r.urgency === 'urgent'
                                  ? 'bg-rose-50 border border-rose-200'
                                  : r.urgency === 'normal'
                                    ? 'bg-brand-leaf-soft'
                                    : 'bg-brand-sun-soft'
                              }`}
                            >
                              <p className="mb-1 flex flex-wrap items-center gap-2">
                                <Link
                                  to={`/users/${r.user_id}?tab=staff-reports`}
                                  className="text-xs font-bold text-ink underline decoration-line-strong underline-offset-2 hover:decoration-brand-leaf"
                                >
                                  {r.user_name ?? `利用者#${r.user_id}`} さんへの支援
                                </Link>
                                {r.staff_name && (
                                  <span className="ml-auto text-[11px] text-ink-faint">記録: {r.staff_name}</span>
                                )}
                              </p>
                              <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">
                                {r.support_content ?? '（記録本文なし）'}
                              </p>
                            </div>
                          ))}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              <p className="mt-3 text-xs text-ink-faint">
                この月の記録: {reports.length}件
              </p>
            </div>
          )}
        </Card>
      ) : reports.length === 0 ? (
        /* ===== 一覧（従来の表示） ===== */
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
                <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-ink">{r.support_content}</p>
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
