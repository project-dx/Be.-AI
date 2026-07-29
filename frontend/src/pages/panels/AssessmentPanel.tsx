import { useEffect, useState } from 'react'
import { assessmentApi, errorMessage, pyramidApi } from '../../services/api'
import { Card, ErrorMessage, Loading } from '../../components/ui'
import { Field, inputClass, PrimaryButton } from '../../components/form'
import { ColorfulPyramidView } from '../../components/ColorfulPyramidView'
import type { Assessment, ColorfulPyramid } from '../../types'

/** アセスメントの記入欄（生育歴・障害特性・思考特性・価値観） */
const FIELDS: { key: keyof Assessment; label: string; hint: string; rows: number }[] = [
  { key: 'life_history', label: '生育歴', hint: '育ってきた環境、学校・就労の経過など', rows: 3 },
  { key: 'disability_characteristics', label: '障害特性', hint: '診断名ではなく、日常でどのような場面に影響が出るか', rows: 3 },
  { key: 'thinking_style', label: '思考特性（ハーマンモデル）の所見', hint: 'どのような考え方・進め方で力を発揮しやすいか', rows: 3 },
  { key: 'personal_values', label: '価値観', hint: '本人が大切にしていること', rows: 2 },
  { key: 'strengths', label: '強み・得意なこと', hint: '', rows: 2 },
  { key: 'support_needs', label: '必要な配慮・支援', hint: '', rows: 2 },
  { key: 'notes', label: 'その他メモ', hint: '', rows: 2 },
]

/** ハーマンモデルの4象限 */
const HERRMANN = [
  { key: 'herrmann_a' as const, label: 'A 論理・分析', color: 'bg-brand-sea', soft: 'bg-brand-sea-soft', text: 'text-brand-sea' },
  { key: 'herrmann_d' as const, label: 'D 創造・全体', color: 'bg-brand-sun', soft: 'bg-brand-sun-soft', text: 'text-brand-sun' },
  { key: 'herrmann_b' as const, label: 'B 堅実・計画', color: 'bg-brand-leaf', soft: 'bg-brand-leaf-soft', text: 'text-brand-leaf' },
  { key: 'herrmann_c' as const, label: 'C 感情・対人', color: 'bg-brand-pink', soft: 'bg-brand-pink-soft', text: 'text-brand-pink' },
]

export default function AssessmentPanel({ userId, canEdit }: { userId: number; canEdit: boolean }) {
  const [assessment, setAssessment] = useState<Partial<Assessment>>({})
  const [pyramid, setPyramid] = useState<Partial<ColorfulPyramid>>({})
  const [loading, setLoading] = useState(true)
  const [savingA, setSavingA] = useState(false)
  const [savingP, setSavingP] = useState(false)
  const [savedA, setSavedA] = useState(false)
  const [savedP, setSavedP] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const ignore404 = (e: unknown) => {
      if ((e as { response?: { status?: number } })?.response?.status === 404) return null
      throw e
    }
    Promise.all([
      assessmentApi.get(userId).catch(ignore404),
      pyramidApi.get(userId).catch(ignore404),
    ])
      .then(([a, p]) => {
        if (a) setAssessment(a)
        if (p) setPyramid(p)
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false))
  }, [userId])

  const saveAssessment = async () => {
    setSavingA(true)
    setError(null)
    try {
      const saved = await assessmentApi.save(userId, assessment)
      setAssessment(saved)
      setSavedA(true)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setSavingA(false)
    }
  }

  const savePyramid = async () => {
    setSavingP(true)
    setError(null)
    try {
      const saved = await pyramidApi.save(userId, pyramid)
      setPyramid(saved)
      setSavedP(true)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setSavingP(false)
    }
  }

  if (loading) return <Card><Loading /></Card>

  const herrmannMax = Math.max(100, ...HERRMANN.map((h) => Number(assessment[h.key] ?? 0)))

  return (
    <div className="space-y-4">
      <ErrorMessage message={error} />

      {/* カラフルピラミッド */}
      <Card title="🔺 カラフルピラミッド" accent="text-brand-coral">
        <p className="mb-4 text-xs text-ink-soft">
          土台のウェルビーイング（幸せを感じるとき）から積み上げて、ミッション（果たしたい役割）までを言葉にします。
          本人の言葉でそのまま書くことを大切にしてください。
        </p>
        <ColorfulPyramidView
          pyramid={pyramid}
          editable
          onChange={(key, value) => { setPyramid((p) => ({ ...p, [key]: value })); setSavedP(false) }}
        />
        <div className="mt-4 flex justify-end">
          <PrimaryButton onClick={savePyramid} disabled={savingP}>
            {savingP ? '保存中…' : savedP ? '保存しました ✓' : 'ピラミッドを保存'}
          </PrimaryButton>
        </div>
      </Card>

      {/* 初期アセスメント */}
      <Card title="🧠 多角的な初期アセスメント" accent="text-brand-plum">
        {!canEdit && (
          <p className="mb-3 rounded-xl bg-paper px-3 py-2 text-xs text-ink-soft">
            閲覧のみです。編集はスタッフ・管理者が行います
          </p>
        )}

        {/* ハーマンモデルの4象限 */}
        <div className="mb-5 rounded-2xl bg-paper p-4">
          <p className="mb-1 text-sm font-bold text-ink">思考特性（ハーマンモデル）の4象限</p>
          <p className="mb-3 text-xs text-ink-soft">
            0〜100で入力します。優劣ではなく「どの考え方で力を発揮しやすいか」の傾向を見るためのものです
          </p>
          <div className="grid grid-cols-2 gap-3">
            {HERRMANN.map((h) => {
              const value = Number(assessment[h.key] ?? 0)
              return (
                <div key={h.key} className={`rounded-2xl p-3 ${h.soft}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-xs font-bold ${h.text}`}>{h.label}</span>
                    <input
                      type="number" min={0} max={100} disabled={!canEdit}
                      aria-label={h.label}
                      value={assessment[h.key] ?? ''}
                      onChange={(e) => {
                        const v = e.target.value === '' ? null : Number(e.target.value)
                        setAssessment((a) => ({ ...a, [h.key]: v }))
                        setSavedA(false)
                      }}
                      className="w-16 rounded-lg border border-line-strong bg-white px-2 py-1 text-right text-sm disabled:opacity-60"
                    />
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/70">
                    <div className={`h-full rounded-full ${h.color} transition-all`} style={{ width: `${(value / herrmannMax) * 100}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="space-y-4">
          {FIELDS.map((f) => (
            <Field key={String(f.key)} label={f.label} hint={f.hint || undefined}>
              <textarea
                rows={f.rows}
                disabled={!canEdit}
                className={`${inputClass} disabled:opacity-70`}
                value={(assessment[f.key] as string | null) ?? ''}
                onChange={(e) => {
                  setAssessment((a) => ({ ...a, [f.key]: e.target.value }))
                  setSavedA(false)
                }}
              />
            </Field>
          ))}
        </div>

        {canEdit && (
          <div className="mt-4 flex items-center justify-end gap-3">
            {assessment.updated_at && (
              <span className="text-xs text-ink-faint">
                最終更新: {new Date(assessment.updated_at).toLocaleString('ja-JP')}
              </span>
            )}
            <PrimaryButton onClick={saveAssessment} disabled={savingA}>
              {savingA ? '保存中…' : savedA ? '保存しました ✓' : 'アセスメントを保存'}
            </PrimaryButton>
          </div>
        )}
      </Card>
    </div>
  )
}
