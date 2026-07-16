import { useEffect, useState } from 'react'
import { errorMessage, reportsApi } from '../services/api'
import { useAuth } from '../stores/AuthContext'
import { Badge, Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { formatDate, mealLabels } from '../utils/labels'
import type { DailyReport } from '../types'

const scaleText = (v: number | null) => (v == null ? '-' : `${v} / 5`)

export default function MyReportsPage() {
  const { user } = useAuth()
  const [reports, setReports] = useState<DailyReport[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [openId, setOpenId] = useState<number | null>(null)

  useEffect(() => {
    if (!user) return
    reportsApi
      .list(user.id, { limit: 60 })
      .then(setReports)
      .catch((e) => setError(errorMessage(e)))
  }, [user])

  if (error) return <ErrorMessage message={error} />
  if (!reports) return <Loading />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-slate-800">📖 過去のふりかえり</h1>
      {reports.length === 0 ? (
        <EmptyState message="まだ日報がありません。「今日の日報」から入力してみましょう" />
      ) : (
        <div className="space-y-3">
          {reports.map((r) => (
            <Card key={r.id}>
              <button
                className="flex w-full items-center justify-between text-left"
                onClick={() => setOpenId(openId === r.id ? null : r.id)}
                aria-expanded={openId === r.id}
              >
                <div className="flex items-center gap-3">
                  <span className="font-bold text-slate-700">{formatDate(r.report_date)}</span>
                  {r.is_draft && <Badge label="下書き" className="bg-amber-100 text-amber-800" />}
                  <span className="text-sm text-slate-500">気分 {scaleText(r.mood)} ／ 睡眠 {r.sleep_hours ?? '-'}時間</span>
                </div>
                <span aria-hidden className="text-slate-400">{openId === r.id ? '▲' : '▼'}</span>
              </button>
              {openId === r.id && (
                <dl className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm border-t border-slate-100 pt-4">
                  <Item label="睡眠の質" value={scaleText(r.sleep_quality)} />
                  <Item label="就寝 / 起床" value={`${r.bedtime ?? '-'} / ${r.wake_time ?? '-'}`} />
                  <Item label="食事" value={`朝: ${mealLabels[r.breakfast_status ?? ''] ?? '-'} ／ 昼: ${mealLabels[r.lunch_status ?? ''] ?? '-'} ／ 夜: ${mealLabels[r.dinner_status ?? ''] ?? '-'}`} />
                  <Item label="運動 / 仕事・勉強" value={`${r.exercise_minutes ?? '-'}分 / ${r.work_study_minutes ?? '-'}分`} />
                  <Item label="ストレス" value={scaleText(r.stress_level)} />
                  <Item label="疲労度" value={scaleText(r.fatigue_level)} />
                  <Item label="人との交流" value={scaleText(r.social_level)} />
                  {r.achievement && <Item label="今日できたこと" value={r.achievement} wide />}
                  {r.success_experience && <Item label="成功体験" value={r.success_experience} wide />}
                  {r.difficulty && <Item label="困ったこと" value={r.difficulty} wide />}
                  {r.tomorrow_goal && <Item label="明日の目標" value={r.tomorrow_goal} wide />}
                  {r.free_text && <Item label="自由記述" value={r.free_text} wide />}
                </dl>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

function Item({ label, value, wide }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={wide ? 'sm:col-span-2' : ''}>
      <dt className="text-xs font-bold text-slate-400">{label}</dt>
      <dd className="text-slate-700 whitespace-pre-wrap">{value}</dd>
    </div>
  )
}
