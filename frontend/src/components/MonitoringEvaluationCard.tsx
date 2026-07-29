import { useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage, monitoringApi } from '../services/api'
import { Card, EmptyState, ErrorMessage } from './ui'
import { PrimaryButton } from './form'
import { LONG_PRESETS, PeriodPicker, daysAgoISO, todayISO } from './PeriodPicker'
import type { MonitoringEvaluation } from '../types'

const DETAIL_FIELDS: { key: keyof MonitoringEvaluation; label: string; chip: string }[] = [
  { key: 'achievements', label: '達成できたこと', chip: 'bg-brand-leaf-soft' },
  { key: 'challenges', label: '残された課題', chip: 'bg-brand-coral-soft' },
  { key: 'plan_adjustments', label: '支援計画の調整', chip: 'bg-brand-sea-soft' },
  { key: 'next_period_focus', label: '次期の重点', chip: 'bg-brand-plum-soft' },
]

/**
 * 定期モニタリング評価（6か月サイクル）。
 * 半期ごとの実績を1000文字以内の総合評価にまとめる（スタッフ・管理者向け）。
 */
export function MonitoringEvaluationCard({ users }: { users: { user_id: number; display_name: string }[] }) {
  const [userId, setUserId] = useState<number | ''>(users[0]?.user_id ?? '')
  const [start, setStart] = useState(daysAgoISO(180))
  const [end, setEnd] = useState(todayISO())
  const [result, setResult] = useState<MonitoringEvaluation | null>(null)
  const [targetName, setTargetName] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    if (userId === '') return
    setRunning(true)
    setError(null)
    try {
      const evaluation = await monitoringApi.generateForPeriod(Number(userId), start, end)
      setResult(evaluation)
      setTargetName(users.find((u) => u.user_id === Number(userId))?.display_name ?? '')
    } catch (e) {
      setError(errorMessage(e))
      setResult(null)
    } finally {
      setRunning(false)
    }
  }

  const scores = result?.score_summary_json?.scores ?? {}

  return (
    <Card title="🔁 定期モニタリング評価（6か月サイクル）" accent="text-brand-sea">
      <p className="mb-3 text-xs text-ink-soft">
        半期ごとの実績をまとめて評価します。期間はカレンダーから自由に選べます。
        評価は日報・支援記録・スコア・目標をもとにした下書きです
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <select
          aria-label="利用者"
          value={userId}
          onChange={(e) => setUserId(e.target.value === '' ? '' : Number(e.target.value))}
          className="rounded-xl border border-line-strong bg-white px-3 py-1.5 text-sm focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15"
        >
          {users.length === 0 && <option value="">利用者がいません</option>}
          {users.map((u) => (
            <option key={u.user_id} value={u.user_id}>{u.display_name}</option>
          ))}
        </select>
        <PeriodPicker
          start={start}
          end={end}
          presets={LONG_PRESETS}
          disabled={running}
          onChange={(s, e) => { setStart(s); setEnd(e) }}
        />
        <PrimaryButton onClick={run} disabled={running || userId === ''}>
          {running ? '作成中…' : '評価をまとめる'}
        </PrimaryButton>
      </div>

      {error && <div className="mt-3"><ErrorMessage message={error} /></div>}

      {result ? (
        <div className="mt-4 space-y-3">
          <p className="text-xs font-bold text-ink-faint">
            {targetName}さん ／ {result.period_start} 〜 {result.period_end}
            {result.score_summary_json && (
              <>（日報 {result.score_summary_json.report_count}件
                {result.score_summary_json.staff_report_count != null &&
                  ` ・支援記録 ${result.score_summary_json.staff_report_count}件`}）
              </>
            )}
          </p>

          {/* 総合評価（1000文字以内） */}
          {result.overall_evaluation && (
            <div className="rounded-2xl border border-brand-sea/25 bg-brand-sea-soft p-4">
              <p className="mb-1.5 text-sm font-bold text-ink">📋 総合評価（半期のまとめ）</p>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{result.overall_evaluation}</p>
              <p className="mt-2 text-right text-[11px] text-ink-faint">{result.overall_evaluation.length}文字</p>
            </div>
          )}

          {/* 日々の状態の可視化（スコアの前半→後半） */}
          {Object.keys(scores).length > 0 && (
            <div>
              <p className="mb-1.5 text-sm font-bold text-ink">📊 日々の状態の推移（期間の前半 → 後半）</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(scores).map(([key, s]) => {
                  const diff = s.diff
                  const tone =
                    diff == null ? 'text-ink-faint'
                      : diff >= 5 ? 'text-brand-leaf'
                        : diff <= -5 ? 'text-brand-coral'
                          : 'text-ink-soft'
                  return (
                    <div key={key} className="rounded-2xl bg-paper px-3 py-2">
                      <p className="text-[11px] font-bold text-ink-faint">{s.label}</p>
                      <p className="text-sm font-bold text-ink">
                        {s.before ?? '—'} <span className="text-ink-faint">→</span> {s.after ?? '—'}
                        {diff != null && (
                          <span className={`ml-1.5 text-xs ${tone}`}>{diff > 0 ? '+' : ''}{diff}</span>
                        )}
                      </p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* 内訳 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
            {DETAIL_FIELDS.map((f) => {
              const text = result[f.key] as string | null
              if (!text) return null
              return (
                <div key={String(f.key)} className={`rounded-2xl p-3.5 ${f.chip}`}>
                  <p className="mb-1 text-xs font-bold text-ink">{f.label}</p>
                  <p className="text-sm leading-relaxed text-ink">{text}</p>
                </div>
              )
            })}
          </div>

          <p className="rounded-xl bg-brand-sun-soft px-3 py-2 text-xs text-ink-soft">
            ⚠️ 自動生成された下書きです。
            <Link to={`/users/${result.user_id}?tab=monitoring`} className="font-bold underline">
              利用者詳細のモニタリングタブ
            </Link>
            から内容を確認・編集してください
          </p>
        </div>
      ) : (
        !running && (
          <div className="mt-4">
            <EmptyState message="利用者と期間を選んで「評価をまとめる」を押すと、半期の総合評価が表示されます" />
          </div>
        )
      )}
    </Card>
  )
}
