import { useEffect, useState } from 'react'
import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom'
import { dashboardApi, errorMessage, usersApi } from '../services/api'
import { Card, ErrorMessage, Loading } from '../components/ui'
import { UserDashboardContent } from './UserDashboardPage'
import DailyReportsPanel from './panels/DailyReportsPanel'
import StaffReportsPanel from './panels/StaffReportsPanel'
import AnalysisPanel from './panels/AnalysisPanel'
import PlansPanel from './panels/PlansPanel'
import ActionsPanel from './panels/ActionsPanel'
import GoalsPage from './GoalsPage'
import { formatDate } from '../utils/labels'
import type { User, UserDashboard } from '../types'

const tabs = [
  { key: 'overview', label: '概要' },
  { key: 'reports', label: '日報' },
  { key: 'staff-reports', label: 'スタッフ日報' },
  { key: 'analyses', label: 'AI分析' },
  { key: 'plans', label: '支援計画' },
  { key: 'history', label: '支援履歴' },
  { key: 'goals', label: '目標' },
]

export default function UserDetailPage() {
  const { userId } = useParams()
  const id = Number(userId)
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') ?? 'overview'
  const [user, setUser] = useState<User | null>(null)
  const [dashboard, setDashboard] = useState<UserDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const flash = (location.state as { flash?: string } | null)?.flash

  useEffect(() => {
    if (!id) return
    usersApi.get(id).then(setUser).catch((e) => setError(errorMessage(e)))
    dashboardApi.forUser(id).then(setDashboard).catch(() => setDashboard(null))
  }, [id])

  if (error) return <ErrorMessage message={error} />
  if (!user) return <Loading />

  return (
    <div className="space-y-4">
      {flash && (
        <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          ✅ {flash}
        </p>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-800">🙂 {user.profile?.display_name ?? user.email}</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            支援開始日: {formatDate(user.profile?.support_start_date)} ／ {user.email}
          </p>
        </div>
        <Link
          to={`/users/${id}/staff-report/new`}
          className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-emerald-700"
        >
          🖊️ スタッフ日報を書く
        </Link>
      </div>

      <nav className="flex gap-1 overflow-x-auto pb-1" aria-label="利用者詳細タブ">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setSearchParams({ tab: t.key })}
            aria-current={tab === t.key ? 'page' : undefined}
            className={`whitespace-nowrap rounded-xl px-4 py-2 text-sm font-bold transition-colors ${
              tab === t.key ? 'bg-emerald-600 text-white' : 'bg-white border border-slate-200 text-slate-500 hover:bg-slate-50'
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === 'overview' &&
        (dashboard ? <UserDashboardContent data={dashboard} /> : <Card><Loading /></Card>)}
      {tab === 'reports' && <DailyReportsPanel userId={id} />}
      {tab === 'staff-reports' && <StaffReportsPanel userId={id} />}
      {tab === 'analyses' && <AnalysisPanel userId={id} />}
      {tab === 'plans' && <PlansPanel userId={id} />}
      {tab === 'history' && <ActionsPanel userId={id} />}
      {tab === 'goals' && <GoalsPage targetUserId={id} />}
    </div>
  )
}
