import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage, risksApi } from '../services/api'
import { Badge, Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { alertTypeLabels, formatDateTime } from '../utils/labels'
import type { RiskAlert } from '../types'

export default function RiskAlertsPage() {
  const [alerts, setAlerts] = useState<RiskAlert[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'open' | 'acknowledged' | 'all'>('open')

  const load = useCallback(() => {
    risksApi
      .list(filter === 'all' ? undefined : filter)
      .then(setAlerts)
      .catch((e) => setError(errorMessage(e)))
  }, [filter])

  useEffect(load, [load])

  const acknowledge = async (id: number) => {
    try {
      await risksApi.acknowledge(id)
      load()
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  if (!alerts) return <Loading />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-slate-800">🔔 リスクアラート</h1>
      <p className="text-sm text-slate-500">
        ルールベースの自動判定です。誤検知の可能性があるため、必ずスタッフによる確認を行ってください。外部への自動通報は行われません
      </p>
      <div className="flex gap-2">
        {(['open', 'acknowledged', 'all'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-xl px-4 py-2 text-sm font-bold ${
              filter === f ? 'bg-emerald-600 text-white' : 'bg-white border border-slate-200 text-slate-500'
            }`}
          >
            {f === 'open' ? '未確認' : f === 'acknowledged' ? '確認済み' : 'すべて'}
          </button>
        ))}
      </div>
      <ErrorMessage message={error} />

      {alerts.length === 0 ? (
        <EmptyState message="該当するアラートはありません" />
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => (
            <Card key={a.id} className={a.severity === 'high' && a.status === 'open' ? 'border-rose-300 border-2' : ''}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge
                      label={a.severity === 'high' ? '重要' : a.severity === 'medium' ? '中' : '低'}
                      className={a.severity === 'high' ? 'bg-rose-600 text-white' : 'bg-amber-200 text-amber-900'}
                    />
                    <Badge
                      label={a.status === 'open' ? '未確認' : '確認済み'}
                      className={a.status === 'open' ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'}
                    />
                    <Link to={`/users/${a.user_id}`} className="font-bold text-slate-800 hover:underline">
                      {a.user_name ?? `利用者 #${a.user_id}`}
                    </Link>
                    <span className="text-xs text-slate-500">{alertTypeLabels[a.alert_type] ?? a.alert_type}</span>
                  </div>
                  <p className="mt-1.5 text-sm text-slate-600">{a.reason}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    発生: {formatDateTime(a.created_at)}
                    {a.acknowledged_at && ` ／ 確認: ${formatDateTime(a.acknowledged_at)}`}
                  </p>
                </div>
                {a.status === 'open' && (
                  <button
                    onClick={() => acknowledge(a.id)}
                    className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-bold text-amber-800 hover:bg-amber-100"
                  >
                    確認済みにする
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
