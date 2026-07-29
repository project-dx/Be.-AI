import { useEffect, useState } from 'react'
import { errorMessage, monitoringApi } from '../../services/api'
import { Card, EmptyState, ErrorMessage, Loading } from '../../components/ui'
import { Field, inputClass, PrimaryButton, SecondaryButton } from '../../components/form'
import { ScoreTrendChart } from '../../components/ScoreTrendChart'
import { formatDate } from '../../utils/labels'
import type { MonitoringEvaluation } from '../../types'

const EDITABLE_FIELDS: { key: keyof MonitoringEvaluation; label: string; hint?: string }[] = [
  { key: 'overall_evaluation', label: '総合評価（半期のまとめ）', hint: '200文字程度。期間全体の実績をまとめた文章です' },
  { key: 'achievements', label: '達成できたこと' },
  { key: 'challenges', label: '残された課題' },
  { key: 'plan_adjustments', label: '支援計画の調整' },
  { key: 'next_period_focus', label: '次期の重点' },
  { key: 'staff_comment', label: 'スタッフ確認コメント', hint: '本人との面談内容や、AIの下書きを修正した点を記録します' },
]

export default function MonitoringPanel({ userId }: { userId: number }) {
  const [rows, setRows] = useState<MonitoringEvaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [draft, setDraft] = useState<Partial<MonitoringEvaluation>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    monitoringApi
      .list(userId)
      .then(setRows)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false))
  }, [userId])

  const generate = async () => {
    setGenerating(true)
    setError(null)
    try {
      const created = await monitoringApi.generate(userId, 6)
      setRows((prev) => [created, ...prev])
      setEditingId(created.id)
      setDraft(created)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setGenerating(false)
    }
  }

  const save = async (id: number) => {
    setSaving(true)
    setError(null)
    try {
      const updated = await monitoringApi.update(userId, id, draft)
      setRows((prev) => prev.map((r) => (r.id === id ? updated : r)))
      setEditingId(null)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Card><Loading /></Card>

  return (
    <div className="space-y-4">
      <ErrorMessage message={error} />

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-bold text-ink">🔁 6か月ごとの継続モニタリング</p>
            <p className="mt-0.5 text-xs text-ink-soft">
              直近6か月のスコア推移・目標・支援記録から評価の下書きを作ります。内容はスタッフが確認・編集してください
            </p>
          </div>
          <PrimaryButton onClick={generate} disabled={generating}>
            {generating ? '作成中…' : '評価の下書きを作成'}
          </PrimaryButton>
        </div>
      </Card>

      {rows.length === 0 ? (
        <Card><EmptyState message="モニタリング評価はまだありません" /></Card>
      ) : (
        rows.map((row) => {
          const isEditing = editingId === row.id
          const scores = row.score_summary_json?.scores ?? {}
          return (
            <Card key={row.id}>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-bold text-ink">{formatDate(row.evaluation_date)} の評価</p>
                  <p className="text-xs text-ink-faint">
                    対象期間: {formatDate(row.period_start)} 〜 {formatDate(row.period_end)}
                    {row.score_summary_json && `（日報 ${row.score_summary_json.report_count}件）`}
                  </p>
                </div>
                {isEditing ? (
                  <div className="flex gap-2">
                    <SecondaryButton onClick={() => setEditingId(null)}>キャンセル</SecondaryButton>
                    <PrimaryButton onClick={() => save(row.id)} disabled={saving}>
                      {saving ? '保存中…' : '保存する'}
                    </PrimaryButton>
                  </div>
                ) : (
                  <SecondaryButton onClick={() => { setEditingId(row.id); setDraft(row) }}>編集する</SecondaryButton>
                )}
              </div>

              {/* スコアの前半→後半比較 */}
              <div className="mb-4">
                <ScoreTrendChart scores={scores} />
              </div>

              <div className="space-y-3">
                {EDITABLE_FIELDS.map((f) => {
                  const value = (isEditing ? draft[f.key] : row[f.key]) as string | null
                  return isEditing ? (
                    <Field key={String(f.key)} label={f.label} hint={f.hint}>
                      <textarea
                        rows={3}
                        className={inputClass}
                        value={value ?? ''}
                        onChange={(e) => setDraft((d) => ({ ...d, [f.key]: e.target.value }))}
                      />
                    </Field>
                  ) : (
                    value && (
                      <div key={String(f.key)}>
                        <p className="text-xs font-bold text-ink-faint">{f.label}</p>
                        <p className="text-sm leading-relaxed text-ink">{value}</p>
                      </div>
                    )
                  )
                })}
              </div>

              {row.ai_generated && !row.staff_comment && (
                <p className="mt-3 rounded-xl bg-brand-sun-soft px-3 py-2 text-xs text-ink-soft">
                  ⚠️ 自動生成された下書きです。スタッフが内容を確認し、必要に応じて編集してください
                </p>
              )}
            </Card>
          )
        })
      )}
    </div>
  )
}
