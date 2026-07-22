import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { dashboardApi, errorMessage, risksApi } from '../services/api'
import { Badge, Card, EmptyState, ErrorMessage, Loading, ScoreCard } from '../components/ui'
import { chartColors, TrendLineChart } from '../components/charts'
import { alertTypeLabels, formatDateTime, planStatusLabels } from '../utils/labels'
import type { AdminDashboard, PlanStatus } from '../types'

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    dashboardApi.admin().then(setData).catch((e) => setError(errorMessage(e)))
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
      <h1 className="text-xl font-bold text-ink">🏢 管理者ダッシュボード</h1>
      <ErrorMessage message={error} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <ScoreCard title="利用者数" icon="👥" color="emerald" value={data.summary.total_users} unit="名" />
        <ScoreCard title="スタッフ数" icon="🧑‍💼" color="sky" value={data.summary.total_staff} unit="名" />
        <ScoreCard title="今日の日報入力率" icon="📝" color="violet" value={data.summary.report_rate_today} unit="%" />
        <ScoreCard title="未確認アラート" icon="🔔" color={data.summary.open_alerts > 0 ? 'rose' : 'emerald'} value={data.summary.open_alerts} unit="件" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="📈 日報入力率の推移（14日間）" className="lg:col-span-2">
          <TrendLineChart
            data={data.input_rate_trend}
            series={[{ key: 'rate', name: '入力率', color: chartColors.green }]}
            yDomain={[0, 100]}
            unit="%"
          />
        </Card>
        <Card title="📋 支援計画の状況">
          {Object.keys(data.plan_status_counts).length === 0 ? (
            <EmptyState message="支援計画はまだありません" />
          ) : (
            <ul className="space-y-2">
              {Object.entries(data.plan_status_counts).map(([status, count]) => {
                const label = planStatusLabels[status as PlanStatus]
                return (
                  <li key={status} className="flex items-center justify-between rounded-xl bg-paper px-4 py-2.5">
                    <Badge label={label?.label ?? status} className={label?.className ?? 'bg-paper-deep text-ink'} />
                    <span className="font-bold text-ink">{count}件</span>
                  </li>
                )
              })}
            </ul>
          )}
        </Card>
      </div>

      <Card title="🔔 リスクアラート（全事業所）" accent="text-amber-700">
        {data.alerts.length === 0 ? (
          <EmptyState message="未確認のアラートはありません" />
        ) : (
          <ul className="space-y-2">
            {data.alerts.map((a) => (
              <li key={a.id} className="flex flex-wrap items-start justify-between gap-2 rounded-xl bg-amber-50 px-4 py-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge
                      label={a.severity === 'high' ? '重要' : '中'}
                      className={a.severity === 'high' ? 'bg-rose-600 text-white' : 'bg-amber-200 text-amber-900'}
                    />
                    <Link to={`/users/${a.user_id}`} className="font-bold text-ink underline decoration-amber-300">
                      {a.user_name ?? `利用者 #${a.user_id}`}
                    </Link>
                    <span className="text-xs text-ink-soft">{alertTypeLabels[a.alert_type] ?? a.alert_type}</span>
                    <span className="text-xs text-ink-faint">{formatDateTime(a.created_at)}</span>
                  </div>
                  <p className="mt-1 text-sm text-ink-soft">{a.reason}</p>
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
    </div>
  )
}
