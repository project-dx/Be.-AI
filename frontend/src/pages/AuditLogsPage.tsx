import { useCallback, useEffect, useState } from 'react'
import { auditApi, errorMessage } from '../services/api'
import { Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { inputClass } from '../components/form'
import { formatDateTime } from '../utils/labels'
import type { AuditLog } from '../types'

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [action, setAction] = useState('')

  const load = useCallback(() => {
    auditApi
      .list(action ? { action } : undefined)
      .then(setLogs)
      .catch((e) => setError(errorMessage(e)))
  }, [action])

  useEffect(() => {
    const timer = setTimeout(load, 300)
    return () => clearTimeout(timer)
  }, [load])

  if (error) return <ErrorMessage message={error} />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-slate-800">📋 監査ログ</h1>
      <input
        type="search"
        aria-label="操作名で絞り込み"
        placeholder="操作名で絞り込み（例: login, report, plan）"
        value={action}
        onChange={(e) => setAction(e.target.value)}
        className={`${inputClass} max-w-sm`}
      />
      {!logs ? (
        <Loading />
      ) : logs.length === 0 ? (
        <EmptyState message="該当する監査ログはありません" />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs text-slate-400">
                  <th className="py-2 pr-3 font-bold">日時</th>
                  <th className="py-2 pr-3 font-bold">操作者</th>
                  <th className="py-2 pr-3 font-bold">操作</th>
                  <th className="py-2 font-bold">対象</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3 whitespace-nowrap text-slate-500">{formatDateTime(log.created_at)}</td>
                    <td className="py-2 pr-3 text-slate-700">{log.actor_email ?? '-'}</td>
                    <td className="py-2 pr-3"><code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">{log.action}</code></td>
                    <td className="py-2 text-slate-500">
                      {log.target_type ? `${log.target_type}${log.target_id ? ` #${log.target_id}` : ''}` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
