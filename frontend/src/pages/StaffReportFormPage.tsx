import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, useParams } from 'react-router-dom'
import { errorMessage, staffReportsApi, usersApi } from '../services/api'
import { staffReportSchema, type StaffReportForm } from '../schemas/forms'
import { Field, inputClass, PrimaryButton, SecondaryButton } from '../components/form'
import { Card, ErrorMessage } from '../components/ui'
import { todayISO, urgencyLabels } from '../utils/labels'
import type { Urgency, User } from '../types'

export default function StaffReportFormPage() {
  const { userId } = useParams()
  const navigate = useNavigate()
  const [target, setTarget] = useState<User | null>(null)
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<StaffReportForm>({
    resolver: zodResolver(staffReportSchema),
    defaultValues: { report_date: todayISO(), urgency: 'normal' },
  })

  useEffect(() => {
    if (userId) usersApi.get(Number(userId)).then(setTarget).catch((e) => setServerError(errorMessage(e)))
  }, [userId])

  const onSubmit = async (values: StaffReportForm) => {
    setServerError(null)
    try {
      await staffReportsApi.create(Number(userId), values as Record<string, unknown>)
      navigate(`/users/${userId}`, { state: { flash: 'スタッフ日報を登録しました' } })
    } catch (err) {
      setServerError(errorMessage(err))
    }
  }

  const urgency = watch('urgency')

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-xl font-bold text-slate-800">🖊️ スタッフ日報（支援記録）</h1>
      <p className="text-sm text-slate-500">
        対象利用者: <span className="font-bold text-slate-700">{target?.profile?.display_name ?? '読み込み中…'}</span>
      </p>
      <ErrorMessage message={serverError} />

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <Card>
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="記録日" required error={errors.report_date?.message}>
                <input type="date" max={todayISO()} className={inputClass} {...register('report_date')} />
              </Field>
              <Field label="支援時間（分）" error={errors.support_minutes?.message}>
                <input type="number" min="0" className={inputClass} {...register('support_minutes')} />
              </Field>
            </div>
            <Field label="支援内容" required error={errors.support_content?.message}>
              <textarea rows={2} className={inputClass} {...register('support_content')} />
            </Field>
            <Field label="利用者の様子" error={errors.user_condition?.message}>
              <textarea rows={2} className={inputClass} {...register('user_condition')} />
            </Field>
            <Field label="会話内容" error={errors.conversation_summary?.message}>
              <textarea rows={2} className={inputClass} {...register('conversation_summary')} />
            </Field>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="良かった点" error={errors.positive_points?.message}>
                <textarea rows={2} className={inputClass} {...register('positive_points')} />
              </Field>
              <Field label="課題" error={errors.issues?.message}>
                <textarea rows={2} className={inputClass} {...register('issues')} />
              </Field>
            </div>
            <Field label="行動変化" error={errors.behavior_changes?.message}>
              <textarea rows={2} className={inputClass} {...register('behavior_changes')} />
            </Field>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="実施した支援方法" error={errors.support_method?.message}>
                <textarea rows={2} className={inputClass} {...register('support_method')} />
              </Field>
              <Field label="利用者の反応" error={errors.user_response?.message}>
                <textarea rows={2} className={inputClass} {...register('user_response')} />
              </Field>
            </div>
            <Field label="次回確認事項" error={errors.next_check?.message}>
              <textarea rows={2} className={inputClass} {...register('next_check')} />
            </Field>
            <Field label="緊急度" required error={errors.urgency?.message}>
              <div className="flex flex-wrap gap-2" role="radiogroup">
                {(Object.keys(urgencyLabels) as Urgency[]).map((key) => (
                  <button
                    key={key}
                    type="button"
                    role="radio"
                    aria-checked={urgency === key}
                    onClick={() => setValue('urgency', key)}
                    className={`rounded-xl border px-4 py-2 text-sm font-bold transition-colors ${
                      urgency === key
                        ? key === 'urgent'
                          ? 'border-rose-600 bg-rose-600 text-white'
                          : 'border-emerald-500 bg-emerald-50 text-emerald-800'
                        : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'
                    }`}
                  >
                    {urgencyLabels[key].label}
                  </button>
                ))}
              </div>
              {urgency === 'urgent' && (
                <p className="mt-1 text-xs font-bold text-rose-600">
                  「至急」はダッシュボードに強調表示され、リスクアラートが作成されます
                </p>
              )}
            </Field>
            <Field label="自由記述" error={errors.free_text?.message}>
              <textarea rows={3} className={inputClass} {...register('free_text')} />
            </Field>
          </div>
        </Card>
        <div className="flex gap-2">
          <PrimaryButton type="submit" disabled={isSubmitting}>
            {isSubmitting ? '登録中…' : '登録する'}
          </PrimaryButton>
          <SecondaryButton type="button" onClick={() => navigate(-1)}>キャンセル</SecondaryButton>
        </div>
      </form>
    </div>
  )
}
