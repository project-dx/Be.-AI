import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { dashboardApi, errorMessage, risksApi } from '../services/api'
import { Badge, Card, EmptyState, ErrorMessage, Loading, ScoreCard } from '../components/ui'
import { alertTypeLabels, formatDate, formatDateTime, stressLabels } from '../utils/labels'
import type { StaffDashboard } from '../types'

export default function StaffDashboardPage() {
  const [data, setData] = useState<StaffDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    dashboardApi.staff().then(setData).catch((e) => setError(errorMessage(e)))
  }, [])

  useEffect(load, [load])

  const acknowledge = async (id: number) => {
    try {
      await risksApi.acknowledge(id)
      load()
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  if (error && !data) return <ErrorMessage message={error} />
  if (!data) return <Loading />

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-slate-800">🏠 スタッフダッシュボード</h1>
      <ErrorMessage message={error} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <ScoreCard title="担当利用者" icon="👥" color="emerald" value={data.summary.assigned_users} unit="名" />
        <ScoreCard title="今日の日報提出" icon="📝" color="sky" value={`${data.summary.reported_today}/${data.summary.assigned_users}`} unit="名" />
        <ScoreCard title="未確認アラート" icon="🔔" color={data.summary.open_alerts > 0 ? 'rose' : 'emerald'} value={data.summary.open_alerts} unit="件" />
        <ScoreCard title="至急の記録（7日）" icon="🚨" color={data.summary.urgent_reports_7d > 0 ? 'rose' : 'emerald'} value={data.summary.urgent_reports_7d} unit="件" />
      </div>

      {/* 至急のスタッフ日報 */}
      {data.urgent_reports.length > 0 && (
        <Card title="🚨 緊急度「至急」の支援記録" accent="text-rose-700" className="border-rose-300 border-2">
          <ul className="space-y-2">
            {data.urgent_reports.map((r) => (
              <li key={r.id} className="rounded-xl bg-rose-50 px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge label="至急" className="bg-rose-600 text-white" />
                  <Link to={`/users/${r.user_id}`} className="font-bold text-slate-800 underline decoration-rose-300 hover:text-rose-700">
                    {r.user_name ?? `利用者 #${r.user_id}`}
                  </Link>
                  <span className="text-xs text-slate-500">{formatDate(r.report_date)}</span>
                </div>
                {r.support_content && <p className="mt-1 text-sm text-slate-600">{r.support_content}</p>}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* リスクアラート */}
      <Card title="🔔 リスクアラート（要確認）" accent="text-amber-700">
        {data.alerts.length === 0 ? (
          <EmptyState message="未確認のアラートはありません" />
        ) : (
          <ul className="space-y-2">
            {data.alerts.map((a) => (
              <li key={a.id} className="flex flex-wrap items-start justify-between gap-2 rounded-xl bg-amber-50 px-4 py-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge
                      label={a.severity === 'high' ? '重要' : a.severity === 'medium' ? '中' : '低'}
                      className={a.severity === 'high' ? 'bg-rose-600 text-white' : 'bg-amber-200 text-amber-900'}
                    />
                    <Link to={`/users/${a.user_id}`} className="font-bold text-slate-800 underline decoration-amber-300 hover:text-amber-700">
                      {a.user_name ?? `利用者 #${a.user_id}`}
                    </Link>
                    <span className="text-xs text-slate-500">{alertTypeLabels[a.alert_type] ?? a.alert_type}</span>
                    <span className="text-xs text-slate-400">{formatDateTime(a.created_at)}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{a.reason}</p>
                </div>
                <button
                  onClick={() => acknowledge(a.id)}
                  className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-bold text-amber-800 hover:bg-amber-100"
                >
                  確認済みにする
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* 担当利用者一覧 */}
      <Card title="👥 担当利用者の状況">
        {data.users.length === 0 ? (
          <EmptyState message="担当利用者が割り当てられていません" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs text-slate-400">
                  <th className="py-2 pr-3 font-bold">利用者</th>
                  <th className="py-2 pr-3 font-bold">最終日報</th>
                  <th className="py-2 pr-3 font-bold">生活リズム</th>
                  <th className="py-2 pr-3 font-bold">睡眠</th>
                  <th className="py-2 pr-3 font-bold">メンタル</th>
                  <th className="py-2 pr-3 font-bold">ストレス</th>
                  <th className="py-2 font-bold">アラート</th>
                </tr>
              </thead>
              <tbody>
                {data.users.map((u) => {
                  const stress = u.latest_score?.stress_status ? stressLabels[u.latest_score.stress_status] : null
                  return (
                    <tr key={u.user_id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-2.5 pr-3">
                        <Link to={`/users/${u.user_id}`} className="font-bold text-emerald-700 hover:underline">
                          {u.display_name}
                        </Link>
                      </td>
                      <td className="py-2.5 pr-3">{formatDate(u.last_report_date)}</td>
                      <td className="py-2.5 pr-3">{u.latest_score?.life_rhythm_score ?? '-'}</td>
                      <td className="py-2.5 pr-3">{u.latest_score?.sleep_score ?? '-'}</td>
                      <td className="py-2.5 pr-3">{u.latest_score?.mental_score ?? '-'}</td>
                      <td className="py-2.5 pr-3">
                        {stress ? <Badge label={`${stress.icon} ${stress.label}`} className={stress.className} /> : '-'}
                      </td>
                      <td className="py-2.5">
                        {u.open_alert_count > 0 ? (
                          <Badge label={`${u.open_alert_count}件`} className="bg-rose-100 text-rose-800" />
                        ) : (
                          <span className="text-slate-400">なし</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
