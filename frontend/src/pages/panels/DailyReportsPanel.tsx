import { useEffect, useState } from 'react'
import { errorMessage, reportsApi, scoresApi } from '../../services/api'
import { Card, EmptyState, ErrorMessage, Loading } from '../../components/ui'
import { formatDate, mealLabels } from '../../utils/labels'
import type { DailyReport } from '../../types'

export default function DailyReportsPanel({ userId }: { userId: number }) {
  const [reports, setReports] = useState<DailyReport[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [openId, setOpenId] = useState<number | null>(null)
  const [recalcMessage, setRecalcMessage] = useState<string | null>(null)

  useEffect(() => {
    reportsApi
      .list(userId, { limit: 60 })
      .then(setReports)
      .catch((e) => setError(errorMessage(e)))
  }, [userId])

  const recalculate = async () => {
    setRecalcMessage(null)
    try {
      const res = await scoresApi.recalculate(userId, 30)
      setRecalcMessage(`スコアを再計算しました（${res.calculated_days}日分）`)
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  if (error && !reports) return <ErrorMessage message={error} />
  if (!reports) return <Loading />

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">直近の日報 {reports.length}件</p>
        <button
          onClick={recalculate}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
        >
          ♻️ スコアを再計算（30日）
        </button>
      </div>
      {recalcMessage && (
        <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800">
          {recalcMessage}
        </p>
      )}
      <ErrorMessage message={error} />
      {reports.length === 0 ? (
        <EmptyState message="日報はまだ入力されていません" />
      ) : (
        reports.map((r) => (
          <Card key={r.id}>
            <button
              className="flex w-full items-center justify-between text-left"
              onClick={() => setOpenId(openId === r.id ? null : r.id)}
              aria-expanded={openId === r.id}
            >
              <span className="flex flex-wrap items-center gap-3 text-sm">
                <span className="font-bold text-slate-700">{formatDate(r.report_date)}</span>
                <span className="text-slate-500">気分 {r.mood ?? '-'}/5</span>
                <span className="text-slate-500">睡眠 {r.sleep_hours ?? '-'}h</span>
                <span className="text-slate-500">ストレス {r.stress_level ?? '-'}/5</span>
              </span>
              <span aria-hidden className="text-slate-400">{openId === r.id ? '▲' : '▼'}</span>
            </button>
            {openId === r.id && (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 border-t border-slate-100 pt-3 text-sm">
                <p><span className="text-xs font-bold text-slate-400 block">就寝 / 起床</span>{r.bedtime ?? '-'} / {r.wake_time ?? '-'}（質 {r.sleep_quality ?? '-'}/5）</p>
                <p><span className="text-xs font-bold text-slate-400 block">食事</span>朝 {mealLabels[r.breakfast_status ?? ''] ?? '-'} ／ 昼 {mealLabels[r.lunch_status ?? ''] ?? '-'} ／ 夜 {mealLabels[r.dinner_status ?? ''] ?? '-'}</p>
                <p><span className="text-xs font-bold text-slate-400 block">運動 / 仕事・勉強</span>{r.exercise_minutes ?? '-'}分 / {r.work_study_minutes ?? '-'}分</p>
                <p><span className="text-xs font-bold text-slate-400 block">疲労 / 交流</span>{r.fatigue_level ?? '-'}/5 ／ {r.social_level ?? '-'}/5</p>
                {r.achievement && <p className="sm:col-span-2"><span className="text-xs font-bold text-slate-400 block">今日できたこと</span>{r.achievement}</p>}
                {r.success_experience && <p className="sm:col-span-2"><span className="text-xs font-bold text-slate-400 block">成功体験</span>{r.success_experience}</p>}
                {r.difficulty && <p className="sm:col-span-2"><span className="text-xs font-bold text-slate-400 block">困ったこと</span>{r.difficulty}</p>}
                {r.tomorrow_goal && <p className="sm:col-span-2"><span className="text-xs font-bold text-slate-400 block">明日の目標</span>{r.tomorrow_goal}</p>}
                {r.free_text && <p className="sm:col-span-2"><span className="text-xs font-bold text-slate-400 block">自由記述</span>{r.free_text}</p>}
              </div>
            )}
          </Card>
        ))
      )}
    </div>
  )
}
