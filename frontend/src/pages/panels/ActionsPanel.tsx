import { useCallback, useEffect, useState } from 'react'
import { actionsApi, errorMessage, plansApi } from '../../services/api'
import { Card, EmptyState, ErrorMessage, Loading } from '../../components/ui'
import { Field, inputClass, PrimaryButton } from '../../components/form'
import { formatDate, todayISO } from '../../utils/labels'
import type { SupportAction, SupportPlan } from '../../types'

const effectLabels: Record<number, string> = {
  1: '効果なし',
  2: 'あまり効果なし',
  3: 'どちらともいえない',
  4: '効果あり',
  5: '大きな効果あり',
}

export default function ActionsPanel({ userId }: { userId: number }) {
  const [actions, setActions] = useState<SupportAction[] | null>(null)
  const [plans, setPlans] = useState<SupportPlan[]>([])
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    action_date: todayISO(),
    action_content: '',
    user_response: '',
    effect_score: '' as string,
    next_action: '',
    support_plan_id: '' as string,
  })
  const [formError, setFormError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    actionsApi.list(userId).then(setActions).catch((e) => setError(errorMessage(e)))
    plansApi.list(userId).then(setPlans).catch(() => setPlans([]))
  }, [userId])

  useEffect(load, [load])

  const submit = async () => {
    if (!form.action_content.trim()) {
      setFormError('支援内容を入力してください')
      return
    }
    setFormError(null)
    setBusy(true)
    try {
      await actionsApi.create(userId, {
        action_date: form.action_date,
        action_content: form.action_content,
        user_response: form.user_response || null,
        effect_score: form.effect_score ? Number(form.effect_score) : null,
        next_action: form.next_action || null,
        support_plan_id: form.support_plan_id ? Number(form.support_plan_id) : null,
      })
      setForm({ ...form, action_content: '', user_response: '', effect_score: '', next_action: '' })
      load()
    } catch (e) {
      setFormError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (error) return <ErrorMessage message={error} />
  if (!actions) return <Loading />

  const planTitle = (id: number | null) => plans.find((p) => p.id === id)?.title ?? null

  return (
    <div className="space-y-4">
      <Card title="➕ 支援実施記録を登録（効果測定）">
        <div className="space-y-3">
          <ErrorMessage message={formError} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="実施日" required>
              <input type="date" max={todayISO()} className={inputClass} value={form.action_date}
                onChange={(e) => setForm({ ...form, action_date: e.target.value })} />
            </Field>
            <Field label="関連する支援計画">
              <select className={inputClass} value={form.support_plan_id}
                onChange={(e) => setForm({ ...form, support_plan_id: e.target.value })}>
                <option value="">（関連付けない）</option>
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </select>
            </Field>
          </div>
          <Field label="実施した支援" required>
            <textarea rows={2} className={inputClass} value={form.action_content}
              onChange={(e) => setForm({ ...form, action_content: e.target.value })} />
          </Field>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="利用者の反応">
              <textarea rows={2} className={inputClass} value={form.user_response}
                onChange={(e) => setForm({ ...form, user_response: e.target.value })} />
            </Field>
            <Field label="効果（1〜5）" hint="支援実施後の変化の実感">
              <select className={inputClass} value={form.effect_score}
                onChange={(e) => setForm({ ...form, effect_score: e.target.value })}>
                <option value="">（未評価）</option>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n}: {effectLabels[n]}</option>
                ))}
              </select>
            </Field>
          </div>
          <Field label="次のアクション">
            <input className={inputClass} value={form.next_action}
              onChange={(e) => setForm({ ...form, next_action: e.target.value })} />
          </Field>
          <PrimaryButton onClick={submit} disabled={busy}>登録する</PrimaryButton>
        </div>
      </Card>

      {actions.length === 0 ? (
        <EmptyState message="支援実施記録はまだありません" />
      ) : (
        <div className="space-y-3">
          {actions.map((a) => (
            <Card key={a.id}>
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-bold text-slate-700">{formatDate(a.action_date)}</span>
                {a.effect_score != null && (
                  <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-800">
                    効果 {a.effect_score}/5（{effectLabels[a.effect_score]}）
                  </span>
                )}
                {planTitle(a.support_plan_id) && (
                  <span className="text-xs text-slate-400">📋 {planTitle(a.support_plan_id)}</span>
                )}
              </div>
              <p className="mt-1.5 text-sm text-slate-700">{a.action_content}</p>
              {a.user_response && <p className="mt-1 text-xs text-slate-500">反応: {a.user_response}</p>}
              {a.next_action && <p className="mt-1 text-xs text-slate-500">次のアクション: {a.next_action}</p>}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
