import { useCallback, useEffect, useMemo, useState } from 'react'
import { errorMessage, monthlyReportsApi } from '../services/api'
import { AiDisclaimer, Card, EmptyState, ErrorMessage, Loading, ScoreCard } from '../components/ui'
import { chartColors, SimpleBarChart } from '../components/charts'
import { PrimaryButton } from '../components/form'
import type { MonthlyReport } from '../types'

function currentYearMonth(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

/** 分布オブジェクトをグラフ用データへ変換（件数の多い順） */
function distToChartData(dist: Record<string, number>): { label: string; count: number }[] {
  return Object.entries(dist)
    .sort((a, b) => b[1] - a[1])
    .map(([label, count]) => ({ label, count }))
}

const USER_SECTION_DEFS = [
  { key: 'mental', label: 'メンタル', icon: '💭', chip: 'bg-brand-sea-soft text-brand-sea' },
  { key: 'condition', label: '体調', icon: '🌡️', chip: 'bg-brand-coral-soft text-brand-coral' },
  { key: 'skill', label: 'スキル', icon: '✏️', chip: 'bg-brand-leaf-soft text-brand-leaf' },
  { key: 'plan', label: '傾向と対策', icon: '🧭', chip: 'bg-brand-plum-soft text-brand-plum' },
] as const

export default function MonthlyReportPage() {
  const [yearMonth, setYearMonth] = useState(currentYearMonth())
  const [report, setReport] = useState<MonthlyReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const load = useCallback((ym: string) => {
    setLoading(true)
    setNotFound(false)
    setError(null)
    monthlyReportsApi
      .latest(ym)
      .then((r) => setReport(r))
      .catch((e) => {
        setReport(null)
        if (e?.response?.status === 404) setNotFound(true)
        else setError(errorMessage(e))
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    load(yearMonth)
  }, [yearMonth, load])

  const generate = async () => {
    setGenerating(true)
    setError(null)
    try {
      const r = await monthlyReportsApi.generate(yearMonth)
      setReport(r)
      setNotFound(false)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setGenerating(false)
    }
  }

  const facts = report?.facts_json
  const result = report?.result_json

  const attendanceDates = useMemo(() => {
    if (!facts) return []
    const dates = new Set<string>()
    for (const a of facts.attendance) {
      a.attended_dates.forEach((d) => dates.add(d))
      a.absence_dates.forEach((d) => dates.add(d))
    }
    return Array.from(dates).sort()
  }, [facts])

  const attendanceRate = useMemo(() => {
    if (!facts || facts.total_users === 0 || attendanceDates.length === 0) return null
    const total = facts.attendance.reduce((sum, a) => sum + a.report_count, 0)
    return Math.round((total / (facts.total_users * attendanceDates.length)) * 100)
  }, [facts, attendanceDates])

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-ink">📊 月次利用者分析レポート</h1>
        <div className="flex items-center gap-2">
          <input
            type="month"
            value={yearMonth}
            max={currentYearMonth()}
            onChange={(e) => setYearMonth(e.target.value)}
            aria-label="対象月"
            className="rounded-2xl border border-line-strong bg-white px-3.5 py-2 text-sm focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15"
          />
          <PrimaryButton onClick={generate} disabled={generating}>
            {generating ? '生成中…' : report ? 'レポートを再生成' : 'レポートを生成'}
          </PrimaryButton>
        </div>
      </div>

      <AiDisclaimer />
      <ErrorMessage message={error} />

      {loading ? (
        <Loading />
      ) : notFound && !report ? (
        <Card>
          <EmptyState message={`${yearMonth.replace('-', '年')}月のレポートはまだ生成されていません。「レポートを生成」を押すと、日報と支援記録をもとにAIが分析します`} />
        </Card>
      ) : report && facts && result ? (
        <>
          {/* サマリーカード */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <ScoreCard title="対象の利用者" icon="👥" color="emerald" value={facts.total_users} unit="名" />
            <ScoreCard title="日報の記録" icon="📝" color="sky" value={facts.total_reports} unit="件" />
            <ScoreCard title="出席率（記録ベース）" icon="🗓️" color="violet" value={attendanceRate ?? '—'} unit="%" />
            <ScoreCard
              title="欠席の記録"
              icon="🏠"
              color="amber"
              value={facts.attendance.reduce((s, a) => s + a.absence_dates.length, 0)}
              unit="回"
            />
          </div>

          {/* 分析ポイント */}
          <Card title="🔍 分析ポイント" accent="text-brand-sea">
            <p className="text-sm leading-relaxed text-ink">{result.analysis_points}</p>
          </Card>

          {/* 出席状況 */}
          <Card title="🗓️ 日次出席状況">
            {attendanceDates.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="overflow-x-auto">
                <table className="text-xs">
                  <thead>
                    <tr>
                      <th className="sticky left-0 bg-white pr-3 py-1.5 text-left font-bold text-ink-soft">利用者</th>
                      {attendanceDates.map((d) => (
                        <th key={d} className="px-1 py-1.5 font-normal text-ink-faint">
                          {Number(d.slice(8, 10))}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {facts.attendance.map((a) => (
                      <tr key={a.user_id} className="border-t border-line">
                        <td className="sticky left-0 bg-white pr-3 py-1.5 font-bold text-ink whitespace-nowrap">
                          {facts.user_names[String(a.user_id)] ?? `利用者#${a.user_id}`}
                        </td>
                        {attendanceDates.map((d) => {
                          const attended = a.attended_dates.includes(d)
                          const absent = a.absence_dates.includes(d)
                          return (
                            <td key={d} className="px-1 py-1.5 text-center">
                              <span
                                aria-label={attended ? '出席' : absent ? '欠席' : '記録なし'}
                                className={`inline-block h-3.5 w-3.5 rounded-full ${
                                  attended ? 'bg-brand-leaf' : absent ? 'bg-brand-coral' : 'bg-paper-deep'
                                }`}
                              />
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-3 flex gap-4 text-xs text-ink-faint">
                  <span><span className="inline-block h-2.5 w-2.5 rounded-full bg-brand-leaf mr-1" />出席（日報あり）</span>
                  <span><span className="inline-block h-2.5 w-2.5 rounded-full bg-brand-coral mr-1" />欠席の記録</span>
                  <span><span className="inline-block h-2.5 w-2.5 rounded-full bg-paper-deep mr-1" />記録なし</span>
                </p>
              </div>
            )}
          </Card>

          {/* 分布グラフ */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card title="🌡️ 体調の分布">
              <SimpleBarChart
                data={distToChartData(facts.condition_distribution)}
                series={[{ key: 'count', name: '日数', color: chartColors.orange }]}
                unit="件"
              />
            </Card>
            <Card title="🙂 気分の分布">
              <SimpleBarChart
                data={distToChartData(facts.mood_distribution)}
                series={[{ key: 'count', name: '日数', color: chartColors.blue }]}
                unit="件"
              />
            </Card>
          </div>

          {/* スキル傾向 */}
          <Card title="✏️ スキル傾向" accent="text-brand-leaf">
            <p className="text-sm leading-relaxed text-ink mb-3">{result.skill_trends}</p>
            {Object.keys(facts.skill_distribution).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {distToChartData(facts.skill_distribution).map(({ label, count }) => (
                  <span key={label} className="rounded-full bg-brand-leaf-soft px-3 py-1 text-xs font-bold text-ink">
                    {label} <span className="text-brand-leaf">{count}件</span>
                  </span>
                ))}
              </div>
            )}
          </Card>

          {/* 利用者別分析 */}
          <h2 className="text-lg font-bold text-ink pt-2">👤 利用者別の分析</h2>
          {result.user_analyses.map((ua) => (
            <Card key={ua.user_id}>
              <h3 className="mb-4 text-base font-bold text-ink">{ua.display_name} さん</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {USER_SECTION_DEFS.map((def) => (
                  <div key={def.key} className="rounded-2xl bg-paper p-4">
                    <p className={`mb-1.5 inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-bold ${def.chip}`}>
                      <span aria-hidden>{def.icon}</span>
                      {def.label}
                    </p>
                    <p className="text-sm leading-relaxed text-ink">{ua[def.key]}</p>
                  </div>
                ))}
              </div>
            </Card>
          ))}

          {/* アクションプラン */}
          <Card title="🚀 翌月に向けたアクションプラン" accent="text-brand-plum">
            <ol className="space-y-3">
              {result.action_plan.map((step, i) => (
                <li key={i} className="flex gap-3.5">
                  <span
                    aria-hidden
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-plum-soft font-display text-sm font-black text-brand-plum"
                  >
                    {i + 1}
                  </span>
                  <div>
                    <p className="text-sm font-bold text-ink">{step.title}</p>
                    <p className="mt-0.5 text-sm leading-relaxed text-ink-soft">{step.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
          </Card>

          {/* データの制約・生成情報 */}
          {result.data_limitations.length > 0 && (
            <p className="text-xs text-ink-faint">
              ※ {result.data_limitations.join(' ／ ')}
            </p>
          )}
          <p className="text-xs text-ink-faint">
            生成: {new Date(report.created_at).toLocaleString('ja-JP')} ／ モデル: {report.model_name}
          </p>
        </>
      ) : null}
    </div>
  )
}
