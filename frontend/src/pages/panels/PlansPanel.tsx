import { useCallback, useEffect, useState } from 'react'
import { errorMessage, plansApi } from '../../services/api'
import { AiDisclaimer, Badge, Card, EmptyState, ErrorMessage, Loading } from '../../components/ui'
import { Field, inputClass, PrimaryButton, SecondaryButton } from '../../components/form'
import { formatDate, formatDateTime, planStatusLabels } from '../../utils/labels'
import type { PlanVersion, SupportPlan } from '../../types'

const listFields: { key: keyof SupportPlan; label: string }[] = [
  { key: 'short_term_goals_json', label: '短期目標' },
  { key: 'support_methods_json', label: '具体的支援方法' },
  { key: 'home_actions_json', label: '家庭でできること' },
  { key: 'office_actions_json', label: '事業所でできること' },
  { key: 'user_actions_json', label: '本人が取り組むこと' },
  { key: 'evaluation_metrics_json', label: '評価指標' },
]

const textFields: { key: keyof SupportPlan; label: string }[] = [
  { key: 'current_issues', label: '現在の課題' },
  { key: 'strengths', label: '利用者の強み' },
  { key: 'user_preferences', label: '本人の希望' },
  { key: 'background_hypothesis', label: '原因・背景の仮説' },
  { key: 'long_term_goal', label: '長期目標' },
  { key: 'notes', label: '注意事項' },
]

export default function PlansPanel({ userId }: { userId: number }) {
  const [plans, setPlans] = useState<SupportPlan[] | null>(null)
  const [selected, setSelected] = useState<SupportPlan | null>(null)
  const [versions, setVersions] = useState<PlanVersion[] | null>(null)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    plansApi
      .list(userId)
      .then((list) => {
        setPlans(list)
        setSelected((prev) => (prev ? list.find((p) => p.id === prev.id) ?? list[0] ?? null : list[0] ?? null))
      })
      .catch((e) => setError(errorMessage(e)))
  }, [userId])

  useEffect(load, [load])

  useEffect(() => {
    setVersions(null)
    setEditing(false)
    if (selected) {
      plansApi.versions(selected.id).then(setVersions).catch(() => setVersions([]))
    }
  }, [selected?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const generate = async () => {
    setBusy(true)
    setError(null)
    try {
      const plan = await plansApi.generate(userId)
      setSelected(plan)
      load()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const startEdit = () => {
    if (!selected) return
    const d: Record<string, string> = { title: selected.title, change_reason: '' }
    for (const { key } of textFields) d[key] = (selected[key] as string | null) ?? ''
    for (const { key } of listFields) d[key] = ((selected[key] as string[] | null) ?? []).join('\n')
    d.next_review_date = selected.next_review_date ?? ''
    d.evaluation_date = selected.evaluation_date ?? ''
    setDraft(d)
    setEditing(true)
  }

  const saveEdit = async () => {
    if (!selected) return
    setBusy(true)
    setError(null)
    try {
      const body: Record<string, unknown> = {
        title: draft.title,
        change_reason: draft.change_reason || '編集',
        next_review_date: draft.next_review_date || null,
        evaluation_date: draft.evaluation_date || null,
      }
      for (const { key } of textFields) body[key] = draft[key] || null
      for (const { key } of listFields)
        body[key] = draft[key].split('\n').map((s) => s.trim()).filter(Boolean)
      const updated = await plansApi.update(selected.id, body)
      setSelected(updated)
      setEditing(false)
      load()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const approve = async () => {
    if (!selected) return
    if (!window.confirm('この支援計画を承認しますか？承認すると正式な計画になります')) return
    setBusy(true)
    try {
      const updated = await plansApi.approve(selected.id)
      setSelected(updated)
      load()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const changeStatus = async (status: string) => {
    if (!selected) return
    setBusy(true)
    try {
      const updated = await plansApi.update(selected.id, { status, change_reason: `状態を変更: ${status}` })
      setSelected(updated)
      load()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (!plans) return <Loading />

  return (
    <div className="space-y-4">
      <AiDisclaimer />
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={generate}
          disabled={busy}
          className="rounded-xl bg-brand-leaf px-4 py-2.5 text-sm font-bold text-white hover:brightness-105 disabled:opacity-50"
        >
          {busy ? '処理中…' : '🤖 AIで下書きを生成（直近30日）'}
        </button>
        {plans.length > 0 && (
          <select
            aria-label="支援計画を選択"
            className="rounded-xl border border-line-strong bg-white px-3 py-2.5 text-sm"
            value={selected?.id ?? ''}
            onChange={(e) => setSelected(plans.find((p) => p.id === Number(e.target.value)) ?? null)}
          >
            {plans.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}（{planStatusLabels[p.status].label}）
              </option>
            ))}
          </select>
        )}
      </div>
      <ErrorMessage message={error} />

      {!selected ? (
        <EmptyState message="支援計画はまだありません。「AIで下書きを生成」から作成できます" />
      ) : editing ? (
        <Card title="✏️ 支援計画の編集">
          <div className="space-y-4">
            <Field label="タイトル" required>
              <input className={inputClass} value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
            </Field>
            {textFields.map(({ key, label }) => (
              <Field key={key} label={label}>
                <textarea rows={2} className={inputClass} value={draft[key]} onChange={(e) => setDraft({ ...draft, [key]: e.target.value })} />
              </Field>
            ))}
            {listFields.map(({ key, label }) => (
              <Field key={key} label={label} hint="1行につき1項目で入力してください">
                <textarea rows={3} className={inputClass} value={draft[key]} onChange={(e) => setDraft({ ...draft, [key]: e.target.value })} />
              </Field>
            ))}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="評価日">
                <input type="date" className={inputClass} value={draft.evaluation_date} onChange={(e) => setDraft({ ...draft, evaluation_date: e.target.value })} />
              </Field>
              <Field label="次回見直し日">
                <input type="date" className={inputClass} value={draft.next_review_date} onChange={(e) => setDraft({ ...draft, next_review_date: e.target.value })} />
              </Field>
            </div>
            <Field label="変更理由" hint="変更履歴に記録されます">
              <input className={inputClass} value={draft.change_reason} onChange={(e) => setDraft({ ...draft, change_reason: e.target.value })} />
            </Field>
            <div className="flex gap-2">
              <PrimaryButton onClick={saveEdit} disabled={busy}>保存する</PrimaryButton>
              <SecondaryButton onClick={() => setEditing(false)}>キャンセル</SecondaryButton>
            </div>
          </div>
        </Card>
      ) : (
        <>
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="font-bold text-ink">{selected.title}</h3>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-faint">
                  <Badge {...planStatusLabels[selected.status]} label={planStatusLabels[selected.status].label} />
                  <span>更新: {formatDateTime(selected.updated_at)}</span>
                  {selected.approved_at && <span>承認: {formatDateTime(selected.approved_at)}</span>}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <SecondaryButton onClick={startEdit}>✏️ 編集</SecondaryButton>
                {(selected.status === 'draft' || selected.status === 'in_review') && (
                  <>
                    {selected.status === 'draft' && (
                      <SecondaryButton onClick={() => changeStatus('in_review')} disabled={busy}>👀 確認中にする</SecondaryButton>
                    )}
                    <PrimaryButton onClick={approve} disabled={busy}>✅ 承認する</PrimaryButton>
                  </>
                )}
                {selected.status === 'approved' && (
                  <PrimaryButton onClick={() => changeStatus('active')} disabled={busy}>▶️ 実施中にする</PrimaryButton>
                )}
                {selected.status === 'active' && (
                  <SecondaryButton onClick={() => changeStatus('evaluated')} disabled={busy}>📊 評価済みにする</SecondaryButton>
                )}
              </div>
            </div>
            {selected.status === 'draft' && (
              <p className="mt-3 rounded-xl bg-amber-50 border border-amber-200 px-4 py-2.5 text-xs text-amber-800">
                この計画はAIが生成した下書きです。スタッフが内容を確認・編集し、承認して初めて正式な支援計画になります
              </p>
            )}
            <dl className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {textFields.map(({ key, label }) => {
                const value = selected[key] as string | null
                if (!value) return null
                return (
                  <div key={key}>
                    <dt className="text-xs font-bold text-ink-faint">{label}</dt>
                    <dd className="whitespace-pre-wrap text-ink">{value}</dd>
                  </div>
                )
              })}
              {listFields.map(({ key, label }) => {
                const value = selected[key] as string[] | null
                if (!value || value.length === 0) return null
                return (
                  <div key={key}>
                    <dt className="text-xs font-bold text-ink-faint">{label}</dt>
                    <dd>
                      <ul className="list-disc pl-5 text-ink space-y-0.5">
                        {value.map((item, i) => <li key={i}>{item}</li>)}
                      </ul>
                    </dd>
                  </div>
                )
              })}
              <div>
                <dt className="text-xs font-bold text-ink-faint">評価日 / 次回見直し日</dt>
                <dd className="text-ink">{formatDate(selected.evaluation_date)} / {formatDate(selected.next_review_date)}</dd>
              </div>
            </dl>
          </Card>

          <Card title="🕘 変更履歴">
            {!versions ? (
              <Loading />
            ) : versions.length === 0 ? (
              <EmptyState message="変更履歴はありません" />
            ) : (
              <ul className="space-y-1.5 text-sm">
                {versions.map((v) => (
                  <li key={v.id} className="flex flex-wrap items-center gap-2 rounded-lg bg-paper px-3 py-2">
                    <Badge label={`v${v.version_number}`} className="bg-paper-deep text-ink" />
                    <span className="text-ink">{v.change_reason ?? '変更'}</span>
                    <span className="ml-auto text-xs text-ink-faint">{formatDateTime(v.created_at)}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
