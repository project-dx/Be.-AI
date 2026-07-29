import { useState } from 'react'
import { analysesApi, errorMessage } from '../services/api'
import { Card, EmptyState, ErrorMessage } from './ui'
import { PrimaryButton } from './form'
import { PeriodPicker, daysAgoISO, todayISO } from './PeriodPicker'
import type { AnalysisResult } from '../types'

/** 6つの心理学・行動科学の理論 */
const THEORIES: { key: keyof AnalysisResult; label: string; icon: string; chip: string; bar: string }[] = [
  { key: 'maslow_analysis', label: 'マズローの5段階欲求', icon: '🔺', chip: 'bg-brand-coral-soft', bar: 'bg-brand-coral' },
  { key: 'adler_analysis', label: 'アドラー心理学', icon: '🤝', chip: 'bg-brand-pink-soft', bar: 'bg-brand-pink' },
  { key: 'perma_analysis', label: 'ポジティブ心理学（PERMA）', icon: '🌟', chip: 'bg-brand-sun-soft', bar: 'bg-brand-sun' },
  { key: 'abc_analysis', label: 'ABA（応用行動分析学）', icon: '🔄', chip: 'bg-brand-leaf-soft', bar: 'bg-brand-leaf' },
  { key: 'choice_theory_analysis', label: '選択理論心理学', icon: '🧭', chip: 'bg-brand-sea-soft', bar: 'bg-brand-sea' },
  { key: 'behavioral_economics_analysis', label: '行動経済学', icon: '🧠', chip: 'bg-brand-plum-soft', bar: 'bg-brand-plum' },
]

/**
 * 期間を選んで6つの心理学理論で分析する（スタッフ・管理者向け）。
 * 利用者本人には表示しない（理論分析はスタッフの支援判断を補助するもの）。
 */
export function TheoryAnalysisCard({ users }: { users: { user_id: number; display_name: string }[] }) {
  const [userId, setUserId] = useState<number | ''>(users[0]?.user_id ?? '')
  const [start, setStart] = useState(daysAgoISO(30))
  const [end, setEnd] = useState(todayISO())
  const [result, setResult] = useState<Partial<AnalysisResult> | null>(null)
  const [analyzedFor, setAnalyzedFor] = useState<string>('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    if (userId === '') return
    setRunning(true)
    setError(null)
    try {
      const analysis = await analysesApi.runForPeriod(Number(userId), start, end)
      setResult(analysis.result_json)
      const name = users.find((u) => u.user_id === Number(userId))?.display_name ?? ''
      setAnalyzedFor(`${name}さん ／ ${start} 〜 ${end}`)
    } catch (e) {
      setError(errorMessage(e))
      setResult(null)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card title="🧠 6つの心理学による期間分析" accent="text-brand-plum">
      <p className="mb-3 text-xs text-ink-soft">
        カレンダーで期間を選ぶと、その期間の日報・支援記録をもとに6つの理論から分析します。
        結果は支援判断を補助する参考情報です
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
        <PeriodPicker start={start} end={end} disabled={running} onChange={(s, e) => { setStart(s); setEnd(e) }} />
        <PrimaryButton onClick={run} disabled={running || userId === ''}>
          {running ? '分析中…' : '分析する'}
        </PrimaryButton>
      </div>

      {error && <div className="mt-3"><ErrorMessage message={error} /></div>}

      {result ? (
        <>
          <p className="mt-4 text-xs font-bold text-ink-faint">{analyzedFor}</p>
          <div className="mt-2 grid grid-cols-1 lg:grid-cols-2 gap-3">
            {THEORIES.map((t) => {
              const text = result[t.key] as string | undefined
              if (!text) return null
              return (
                <div key={String(t.key)} className={`rounded-2xl p-4 ${t.chip}`}>
                  <p className="mb-1.5 flex items-center gap-1.5 text-sm font-bold text-ink">
                    <span aria-hidden>{t.icon}</span>
                    {t.label}
                  </p>
                  <p className="text-sm leading-relaxed text-ink">{text}</p>
                </div>
              )
            })}
          </div>
          {result.summary && (
            <p className="mt-3 rounded-2xl bg-paper px-4 py-3 text-sm text-ink">
              <span className="text-xs font-bold text-ink-faint block mb-0.5">全体の要約</span>
              {result.summary}
            </p>
          )}
        </>
      ) : (
        !running && (
          <div className="mt-4">
            <EmptyState message="利用者と期間を選んで「分析する」を押すと、6つの理論による分析が表示されます" />
          </div>
        )
      )}
    </Card>
  )
}
