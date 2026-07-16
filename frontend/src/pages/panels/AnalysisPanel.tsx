import { useCallback, useEffect, useState } from 'react'
import { analysesApi, errorMessage } from '../../services/api'
import { AiDisclaimer, Badge, Card, EmptyState, ErrorMessage, Loading } from '../../components/ui'
import { formatDateTime, priorityLabels } from '../../utils/labels'
import type { AiAnalysis } from '../../types'

const theoryLabels: [keyof NonNullable<AiAnalysis['result_json']>, string][] = [
  ['maslow_analysis', 'マズローの欲求5段階'],
  ['adler_analysis', 'アドラー心理学'],
  ['perma_analysis', 'ポジティブ心理学（PERMA）'],
  ['abc_analysis', 'ABC分析（応用行動分析）'],
  ['choice_theory_analysis', '選択理論'],
  ['behavioral_economics_analysis', '行動経済学'],
]

export default function AnalysisPanel({ userId }: { userId: number }) {
  const [analyses, setAnalyses] = useState<AiAnalysis[] | null>(null)
  const [selected, setSelected] = useState<AiAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)

  const load = useCallback(() => {
    analysesApi
      .list(userId)
      .then((list) => {
        setAnalyses(list)
        setSelected((prev) => prev ?? list[0] ?? null)
      })
      .catch((e) => setError(errorMessage(e)))
  }, [userId])

  useEffect(load, [load])

  const run = async () => {
    setRunning(true)
    setError(null)
    try {
      const result = await analysesApi.run(userId, 14)
      setSelected(result)
      load()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setRunning(false)
    }
  }

  if (!analyses) return <Loading />
  const r = selected?.result_json

  return (
    <div className="space-y-4">
      <AiDisclaimer />
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={run}
          disabled={running}
          className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {running ? '分析中…（少しお待ちください）' : '🤖 AI分析を実行（直近14日）'}
        </button>
        {analyses.length > 0 && (
          <select
            aria-label="過去の分析を選択"
            className="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm"
            value={selected?.id ?? ''}
            onChange={(e) => setSelected(analyses.find((a) => a.id === Number(e.target.value)) ?? null)}
          >
            {analyses.map((a) => (
              <option key={a.id} value={a.id}>
                {formatDateTime(a.created_at)}（{a.model_name}）
              </option>
            ))}
          </select>
        )}
      </div>
      <ErrorMessage message={error} />

      {!selected || !r ? (
        <EmptyState message="AI分析はまだ実行されていません。上のボタンから実行できます" />
      ) : (
        <div className="space-y-4">
          {selected.status === 'fallback' && (
            <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
              ⚠️ AI呼び出しに失敗したため、ルールベースの参考情報を表示しています
            </p>
          )}
          <Card title="📄 要約" accent="text-emerald-700">
            <p className="text-sm text-slate-700">{r.summary}</p>
            {r.confidence != null && (
              <p className="mt-2 text-xs text-slate-400">確信度: {Math.round((r.confidence ?? 0) * 100)}%（参考値）</p>
            )}
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card title="💪 強み" accent="text-sky-700">
              {(r.strengths ?? []).length === 0 ? (
                <EmptyState message="記録された強みはありません" />
              ) : (
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {r.strengths?.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              )}
            </Card>
            <Card title="👀 気になる傾向" accent="text-amber-700">
              {(r.concerns ?? []).length === 0 ? (
                <p className="text-sm text-slate-500">大きな懸念は検出されていません</p>
              ) : (
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {r.concerns?.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              )}
            </Card>
          </div>

          {r.trend_analysis && (
            <Card title="📈 推移の分析">
              <p className="text-sm text-slate-700">{r.trend_analysis}</p>
            </Card>
          )}

          {(r.risk_flags ?? []).length > 0 && (
            <Card title="🚩 リスクフラグ（スタッフによる確認が必要）" accent="text-rose-700" className="border-rose-200 border-2">
              <ul className="space-y-1 text-sm text-slate-700">
                {r.risk_flags?.map((f, i) => (
                  <li key={i}>・{f.detail}</li>
                ))}
              </ul>
            </Card>
          )}

          <Card title="🧑‍💼 スタッフ向け提案" accent="text-violet-700">
            {(r.staff_recommendations ?? []).length === 0 ? (
              <EmptyState message="スタッフ向け提案はありません" />
            ) : (
              <div className="space-y-3">
                {r.staff_recommendations?.map((rec, i) => {
                  const priority = priorityLabels[rec.priority] ?? priorityLabels.medium
                  return (
                    <div key={i} className="rounded-xl border border-violet-100 bg-violet-50/40 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-bold text-slate-800 text-sm">{rec.title}</p>
                        <Badge label={priority.label} className={priority.className} />
                        {rec.next_check_date && (
                          <span className="text-xs text-slate-400">次回確認: {rec.next_check_date}</span>
                        )}
                      </div>
                      <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="rounded-lg bg-white p-3 border border-slate-100">
                          <p className="font-bold text-slate-500 mb-1">✅ 確認できる事実</p>
                          {(rec.observed_facts ?? []).length > 0 ? (
                            <ul className="list-disc pl-4 space-y-0.5 text-slate-700">
                              {rec.observed_facts.map((f, j) => <li key={j}>{f}</li>)}
                            </ul>
                          ) : (
                            <p className="text-slate-400">記載なし</p>
                          )}
                        </div>
                        <div className="rounded-lg bg-white p-3 border border-slate-100">
                          <p className="font-bold text-slate-500 mb-1">💭 AIによる仮説</p>
                          <p className="text-slate-700">{rec.hypothesis || '記載なし'}</p>
                        </div>
                      </div>
                      <dl className="mt-2 space-y-1 text-xs text-slate-600">
                        <div><dt className="inline font-bold">推奨する支援: </dt><dd className="inline">{rec.action}</dd></div>
                        <div><dt className="inline font-bold">理由: </dt><dd className="inline">{rec.reason}</dd></div>
                        {(rec.questions ?? []).length > 0 && (
                          <div><dt className="inline font-bold">確認すべき質問: </dt><dd className="inline">{rec.questions.join(' ／ ')}</dd></div>
                        )}
                        {rec.avoid && (
                          <div><dt className="inline font-bold text-rose-600">避けた方がよい対応: </dt><dd className="inline">{rec.avoid}</dd></div>
                        )}
                      </dl>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>

          <Card title="🙂 利用者向け提案（最大3件）" accent="text-emerald-700">
            {(r.user_recommendations ?? []).length === 0 ? (
              <EmptyState message="利用者向け提案はありません" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {r.user_recommendations?.map((rec, i) => (
                  <div key={i} className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 text-xs">
                    <p className="font-bold text-emerald-900 text-sm mb-1.5">{rec.title}</p>
                    <p><span className="font-bold">やること:</span> {rec.action}</p>
                    <p><span className="font-bold">なぜ:</span> {rec.reason}</p>
                    {rec.amount && <p><span className="font-bold">どのくらい:</span> {rec.amount}</p>}
                    {rec.alternative && <p><span className="font-bold">代替案:</span> {rec.alternative}</p>}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="🧠 理論に基づく分析">
            <dl className="space-y-3 text-sm">
              {theoryLabels.map(([key, label]) => {
                const value = r[key]
                if (!value || typeof value !== 'string') return null
                return (
                  <div key={String(key)}>
                    <dt className="text-xs font-bold text-slate-400">{label}</dt>
                    <dd className="text-slate-700">{value}</dd>
                  </div>
                )
              })}
            </dl>
          </Card>

          {(r.data_limitations ?? []).length > 0 && (
            <Card title="⚠️ データの制約">
              <ul className="list-disc pl-5 text-xs text-slate-500 space-y-1">
                {r.data_limitations?.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
