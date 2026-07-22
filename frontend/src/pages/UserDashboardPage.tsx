import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { dashboardApi, errorMessage } from '../services/api'
import { useAuth } from '../stores/AuthContext'
import { AiDisclaimer, Badge, Card, EmptyState, ErrorMessage, Loading, ProgressBar, ScoreCard } from '../components/ui'
import { chartColors, SimpleBarChart, TrendLineChart } from '../components/charts'
import { planStatusLabels, stressLabels } from '../utils/labels'
import type { UserDashboard } from '../types'

export function UserDashboardContent({ data, showUserCta = false }: { data: UserDashboard; showUserCta?: boolean }) {
  const score = data.latest_score
  const stress = score?.stress_status ? stressLabels[score.stress_status] : null
  const recommendations = data.latest_analysis?.result?.user_recommendations ?? []

  return (
    <div className="space-y-5">
      {showUserCta && !data.today_report.exists && (
        <Link
          to="/daily-report"
          className="block rounded-2xl bg-brand-leaf px-5 py-4 text-white hover:brightness-105"
        >
          <p className="font-bold">📝 今日の日報がまだです</p>
          <p className="text-sm text-emerald-100 mt-0.5">3分くらいで入力できます。タップして始めましょう →</p>
        </Link>
      )}
      {showUserCta && data.today_report.exists && data.today_report.is_draft && (
        <Link
          to="/daily-report"
          className="block rounded-2xl bg-amber-500 px-5 py-4 text-white hover:bg-amber-600"
        >
          <p className="font-bold">✍️ 日報が下書きのままです</p>
          <p className="text-sm text-amber-100 mt-0.5">続きを入力して送信しましょう →</p>
        </Link>
      )}

      {/* スコアカード */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
        <ScoreCard title="生活リズムスコア" icon="⏰" color="emerald" value={score?.life_rhythm_score} />
        <ScoreCard title="睡眠スコア" icon="😴" color="sky" value={score?.sleep_score} />
        <ScoreCard title="メンタルスコア" icon="💙" color="violet" value={score?.mental_score} />
        <ScoreCard title="幸福度（PERMA）" icon="🌈" color="pink" value={score?.wellbeing_score} />
        <ScoreCard title="自己効力感" icon="💪" color="amber" value={score?.self_efficacy_score} />
        <ScoreCard title="就労準備度" icon="🏢" color="emerald" value={score?.work_readiness_score} />
        <div className="flex items-center gap-3 rounded-2xl bg-white border border-line p-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-rose-100 text-xl" aria-hidden>
            {stress?.icon ?? '📊'}
          </div>
          <div>
            <p className="text-xs font-bold text-ink-soft">ストレス状態</p>
            {stress ? (
              <Badge label={stress.label} className={stress.className} />
            ) : (
              <p className="text-sm text-ink-faint">データなし</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-2xl bg-white border border-line p-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xl" aria-hidden>🎯</div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-ink-soft">目標達成率</p>
            {data.goal_achievement_rate == null ? (
              <p className="text-sm text-ink-faint">目標なし</p>
            ) : (
              <p className="text-2xl font-bold text-sky-700">{data.goal_achievement_rate}<span className="text-xs font-normal text-ink-soft">%</span></p>
            )}
          </div>
        </div>
      </div>

      {/* 今日の提案 */}
      <Card title="🌟 今日の提案" accent="text-brand-leaf">
        {recommendations.length === 0 ? (
          <EmptyState message="AI分析が実行されると、今日できる小さな提案が表示されます" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {recommendations.slice(0, 3).map((rec, i) => (
              <div key={i} className="rounded-xl border border-emerald-100 bg-brand-leaf-soft/50 p-4">
                <p className="font-bold text-emerald-900 text-sm">{rec.title}</p>
                <dl className="mt-2 space-y-1.5 text-xs text-ink-soft">
                  <div><dt className="inline font-bold">やること: </dt><dd className="inline">{rec.action}</dd></div>
                  <div><dt className="inline font-bold">なぜ: </dt><dd className="inline">{rec.reason}</dd></div>
                  {rec.amount && <div><dt className="inline font-bold">どのくらい: </dt><dd className="inline">{rec.amount}</dd></div>}
                  {rec.alternative && <div><dt className="inline font-bold">むずかしいときは: </dt><dd className="inline">{rec.alternative}</dd></div>}
                </dl>
              </div>
            ))}
          </div>
        )}
        <div className="mt-3">
          <AiDisclaimer />
        </div>
      </Card>

      {/* 支援計画・目標 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="📋 支援計画の進捗">
          {data.support_plan ? (
            <div className="space-y-2">
              <p className="font-bold text-ink text-sm">{data.support_plan.title}</p>
              <Badge {...planStatusLabels[data.support_plan.status]} label={planStatusLabels[data.support_plan.status].label} />
              {data.support_plan.next_review_date && (
                <p className="text-xs text-ink-soft">次回見直し日: {data.support_plan.next_review_date}</p>
              )}
            </div>
          ) : (
            <EmptyState message="支援計画はまだ登録されていません" />
          )}
        </Card>
        <Card title="🎯 目標">
          {data.goals.length === 0 ? (
            <EmptyState message="目標はまだ登録されていません" />
          ) : (
            <div className="space-y-3">
              {data.goals.slice(0, 3).map((g) => (
                <ProgressBar key={g.id} value={g.progress} label={g.title} />
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* グラフ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="😴 睡眠時間の推移（時間）">
          <TrendLineChart
            data={data.sleep_history}
            series={[{ key: 'sleep_hours', name: '睡眠時間', color: chartColors.blue }]}
            yDomain={[0, 12]}
          />
        </Card>
        <Card title="⏰ 生活リズムスコアの推移">
          <TrendLineChart
            data={data.score_history}
            xKey="score_date"
            series={[{ key: 'life_rhythm_score', name: '生活リズム', color: chartColors.green }]}
            yDomain={[0, 100]}
          />
        </Card>
        <Card title="🌈 幸福度（PERMA）の推移">
          <SimpleBarChart
            data={data.score_history}
            xKey="score_date"
            series={[{ key: 'wellbeing_score', name: '幸福度', color: chartColors.pink }]}
            yDomain={[0, 100]}
          />
        </Card>
        <Card title="⚡ ストレスの推移（1〜5）">
          <TrendLineChart
            data={data.stress_history}
            series={[{ key: 'stress_level', name: 'ストレス', color: chartColors.orange }]}
            yDomain={[1, 5]}
          />
        </Card>
        <Card title="📝 日報入力率（週別）" className="lg:col-span-2">
          <SimpleBarChart
            data={data.input_rates_weekly}
            series={[{ key: 'rate', name: '入力率', color: chartColors.violet }]}
            yDomain={[0, 100]}
            unit="%"
            height={180}
          />
        </Card>
      </div>
    </div>
  )
}

export default function UserDashboardPage() {
  const { user } = useAuth()
  const location = useLocation()
  const [data, setData] = useState<UserDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const flash = (location.state as { flash?: string } | null)?.flash

  useEffect(() => {
    dashboardApi.user().then(setData).catch((e) => setError(errorMessage(e)))
  }, [])

  if (error) return <ErrorMessage message={error} />
  if (!data) return <Loading />

  return (
    <div className="space-y-4">
      {flash && (
        <p role="status" className="rounded-xl border border-emerald-200 bg-brand-leaf-soft px-4 py-3 text-sm text-emerald-800">
          ✅ {flash}
        </p>
      )}
      <h1 className="text-xl font-bold text-ink">
        こんにちは、{user?.profile?.display_name ?? ''}さん 🌱
      </h1>
      <UserDashboardContent data={data} showUserCta />
    </div>
  )
}
