import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage, reportsApi } from '../services/api'
import { useAuth } from '../stores/AuthContext'
import {
  dailyReportSchema,
  requiredOnSubmit,
  type DailyReportForm,
  type DailyReportPayload,
} from '../schemas/forms'
import { Field, inputClass, MealInput, PrimaryButton, ScaleInput, SecondaryButton } from '../components/form'
import { Card, ErrorMessage, Loading } from '../components/ui'
import { todayISO } from '../utils/labels'
import axios from 'axios'

const emptyForm: DailyReportForm = {
  report_date: todayISO(),
  mood: null,
  sleep_hours: '',
  bedtime: '',
  wake_time: '',
  sleep_quality: null,
  breakfast_status: '',
  lunch_status: '',
  dinner_status: '',
  exercise_minutes: '',
  work_study_minutes: '',
  stress_level: null,
  fatigue_level: null,
  social_level: null,
  achievement: '',
  success_experience: '',
  difficulty: '',
  tomorrow_goal: '',
  free_text: '',
}

const steps = ['きぶん・すいみん', 'しょくじ・かつどう', 'こころ・からだ', 'きょうのふりかえり']

export default function DailyReportFormPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<DailyReportForm>(emptyForm)
  const [existingId, setExistingId] = useState<number | null>(null)
  const [existingIsDraft, setExistingIsDraft] = useState(false)
  const [step, setStep] = useState(0)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [confirmUpdate, setConfirmUpdate] = useState(false)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [savedMessage, setSavedMessage] = useState<string | null>(null)

  const set = <K extends keyof DailyReportForm>(key: K, value: DailyReportForm[K]) => {
    setForm((f) => ({ ...f, [key]: value }))
    setErrors((e) => ({ ...e, [key]: '' }))
  }

  const loadExisting = useCallback(
    async (date: string) => {
      if (!user) return
      setLoading(true)
      setExistingId(null)
      setConfirmUpdate(false)
      try {
        const reports = await reportsApi.list(user.id, { from: date, to: date })
        const existing = reports[0]
        if (existing) {
          setExistingId(existing.id)
          setExistingIsDraft(existing.is_draft)
          setForm({
            report_date: existing.report_date,
            mood: existing.mood,
            sleep_hours: existing.sleep_hours ?? '',
            bedtime: existing.bedtime ?? '',
            wake_time: existing.wake_time ?? '',
            sleep_quality: existing.sleep_quality,
            breakfast_status: existing.breakfast_status ?? '',
            lunch_status: existing.lunch_status ?? '',
            dinner_status: existing.dinner_status ?? '',
            exercise_minutes: existing.exercise_minutes ?? '',
            work_study_minutes: existing.work_study_minutes ?? '',
            stress_level: existing.stress_level,
            fatigue_level: existing.fatigue_level,
            social_level: existing.social_level,
            achievement: existing.achievement ?? '',
            success_experience: existing.success_experience ?? '',
            difficulty: existing.difficulty ?? '',
            tomorrow_goal: existing.tomorrow_goal ?? '',
            free_text: existing.free_text ?? '',
          })
        } else {
          setForm({ ...emptyForm, report_date: date })
        }
      } catch (err) {
        setServerError(errorMessage(err))
      } finally {
        setLoading(false)
      }
    },
    [user],
  )

  useEffect(() => {
    loadExisting(todayISO())
  }, [loadExisting])

  const validate = (isDraft: boolean): DailyReportPayload | null => {
    const parsed = dailyReportSchema.safeParse(form)
    if (!parsed.success) {
      const map: Record<string, string> = {}
      for (const issue of parsed.error.issues) {
        const key = String(issue.path[0] ?? '')
        if (key && !map[key]) map[key] = issue.message
      }
      setErrors(map)
      setServerError('入力内容に誤りがあります。赤色の項目を確認してください')
      return null
    }
    if (!isDraft) {
      const missing = requiredOnSubmit.filter(({ key }) => parsed.data[key] == null)
      if (missing.length > 0) {
        const map: Record<string, string> = {}
        for (const { key, label } of missing) map[String(key)] = `${label}を入力してください`
        setErrors(map)
        setServerError(`未入力の項目があります: ${missing.map((m) => m.label).join('、')}`)
        return null
      }
    }
    setErrors({})
    setServerError(null)
    return parsed.data
  }

  const save = async (isDraft: boolean, confirmedUpdate = false) => {
    if (!user) return
    const payload = validate(isDraft)
    if (!payload) return

    // 既存の確定済み日報を上書きする場合は確認を挟む
    if (existingId && !existingIsDraft && !confirmedUpdate) {
      setConfirmUpdate(true)
      return
    }

    setSaving(true)
    setSavedMessage(null)
    try {
      const body = { ...payload, is_draft: isDraft }
      if (existingId) {
        const { report_date: _date, ...updateBody } = body
        await reportsApi.update(user.id, existingId, updateBody)
      } else {
        await reportsApi.create(user.id, body)
      }
      if (isDraft) {
        setSavedMessage('下書きを保存しました。あとから続きを入力できます')
        await loadExisting(form.report_date)
      } else {
        navigate('/dashboard', { state: { flash: '日報を送信しました。おつかれさまでした！' } })
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setServerError('この日付の日報は既に存在します。ページを読み込み直してから更新してください')
      } else {
        setServerError(errorMessage(err))
      }
    } finally {
      setSaving(false)
      setConfirmUpdate(false)
    }
  }

  if (loading) return <Loading />

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-xl font-bold text-slate-800">📝 今日の日報</h1>
        <p className="text-sm text-slate-500 mt-1">3分くらいで入力できます。途中で「下書き保存」もできます</p>
      </div>

      <ErrorMessage message={serverError} />
      {savedMessage && (
        <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          ✅ {savedMessage}
        </p>
      )}
      {existingId && !existingIsDraft && (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          この日付の日報は送信済みです。保存すると内容が更新されます
        </p>
      )}

      {confirmUpdate && (
        <div role="alertdialog" aria-label="更新の確認" className="rounded-xl border-2 border-amber-400 bg-white p-4 space-y-3">
          <p className="text-sm font-bold text-slate-700">送信済みの日報を更新しますか？</p>
          <p className="text-sm text-slate-500">この日付の日報は既に送信されています。内容を上書きして更新します。</p>
          <div className="flex gap-2">
            <PrimaryButton onClick={() => save(false, true)} disabled={saving}>更新する</PrimaryButton>
            <SecondaryButton onClick={() => setConfirmUpdate(false)}>キャンセル</SecondaryButton>
          </div>
        </div>
      )}

      {/* ステップ表示 */}
      <nav aria-label="入力ステップ" className="flex gap-1.5">
        {steps.map((label, i) => (
          <button
            key={label}
            onClick={() => setStep(i)}
            aria-current={step === i ? 'step' : undefined}
            className={`flex-1 rounded-xl px-1 py-2 text-xs font-bold transition-colors ${
              step === i ? 'bg-emerald-600 text-white' : i < step ? 'bg-emerald-100 text-emerald-800' : 'bg-white border border-slate-200 text-slate-400'
            }`}
          >
            {i + 1}. {label}
          </button>
        ))}
      </nav>

      <Card>
        <div className="space-y-5">
          {step === 0 && (
            <>
              <Field label="日付" required error={errors.report_date}>
                <input
                  type="date"
                  className={inputClass}
                  value={form.report_date}
                  max={todayISO()}
                  onChange={(e) => {
                    set('report_date', e.target.value)
                    if (e.target.value) loadExisting(e.target.value)
                  }}
                />
              </Field>
              <Field label="今日の気分" required error={errors.mood}>
                <ScaleInput name="今日の気分" value={form.mood ?? null} onChange={(v) => set('mood', v)} lowLabel="つらい" highLabel="とても良い" />
              </Field>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="睡眠時間（時間）" required error={errors.sleep_hours}>
                  <input type="number" step="0.5" min="0" max="24" className={inputClass} value={form.sleep_hours ?? ''} onChange={(e) => set('sleep_hours', e.target.value === '' ? '' : Number(e.target.value))} />
                </Field>
                <Field label="就寝時刻" error={errors.bedtime}>
                  <input type="time" className={inputClass} value={form.bedtime ?? ''} onChange={(e) => set('bedtime', e.target.value)} />
                </Field>
                <Field label="起床時刻" error={errors.wake_time}>
                  <input type="time" className={inputClass} value={form.wake_time ?? ''} onChange={(e) => set('wake_time', e.target.value)} />
                </Field>
              </div>
              <Field label="睡眠の質" required error={errors.sleep_quality}>
                <ScaleInput name="睡眠の質" value={form.sleep_quality ?? null} onChange={(v) => set('sleep_quality', v)} lowLabel="眠れなかった" highLabel="ぐっすり" />
              </Field>
            </>
          )}

          {step === 1 && (
            <>
              <Field label="朝食" error={errors.breakfast_status}>
                <MealInput value={form.breakfast_status || null} onChange={(v) => set('breakfast_status', v)} />
              </Field>
              <Field label="昼食" error={errors.lunch_status}>
                <MealInput value={form.lunch_status || null} onChange={(v) => set('lunch_status', v)} />
              </Field>
              <Field label="夕食" error={errors.dinner_status}>
                <MealInput value={form.dinner_status || null} onChange={(v) => set('dinner_status', v)} />
              </Field>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="運動時間（分）" error={errors.exercise_minutes}>
                  <input type="number" min="0" max="1440" className={inputClass} value={form.exercise_minutes ?? ''} onChange={(e) => set('exercise_minutes', e.target.value === '' ? '' : Number(e.target.value))} />
                </Field>
                <Field label="仕事・勉強時間（分）" error={errors.work_study_minutes}>
                  <input type="number" min="0" max="1440" className={inputClass} value={form.work_study_minutes ?? ''} onChange={(e) => set('work_study_minutes', e.target.value === '' ? '' : Number(e.target.value))} />
                </Field>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <Field label="ストレス" required error={errors.stress_level}>
                <ScaleInput name="ストレス" reverse value={form.stress_level ?? null} onChange={(v) => set('stress_level', v)} lowLabel="なし" highLabel="とても強い" />
              </Field>
              <Field label="疲労度" required error={errors.fatigue_level}>
                <ScaleInput name="疲労度" reverse value={form.fatigue_level ?? null} onChange={(v) => set('fatigue_level', v)} lowLabel="元気" highLabel="とても疲れた" />
              </Field>
              <Field label="人との交流" required error={errors.social_level}>
                <ScaleInput name="人との交流" value={form.social_level ?? null} onChange={(v) => set('social_level', v)} lowLabel="少なかった" highLabel="たくさんあった" />
              </Field>
            </>
          )}

          {step === 3 && (
            <>
              <Field label="今日できたこと" error={errors.achievement} hint="小さなことで大丈夫です">
                <textarea rows={2} className={inputClass} value={form.achievement ?? ''} onChange={(e) => set('achievement', e.target.value)} />
              </Field>
              <Field label="成功体験" error={errors.success_experience}>
                <textarea rows={2} className={inputClass} value={form.success_experience ?? ''} onChange={(e) => set('success_experience', e.target.value)} />
              </Field>
              <Field label="困ったこと" error={errors.difficulty}>
                <textarea rows={2} className={inputClass} value={form.difficulty ?? ''} onChange={(e) => set('difficulty', e.target.value)} />
              </Field>
              <Field label="明日の目標" error={errors.tomorrow_goal} hint="1つだけでOKです">
                <textarea rows={2} className={inputClass} value={form.tomorrow_goal ?? ''} onChange={(e) => set('tomorrow_goal', e.target.value)} />
              </Field>
              <Field label="自由記述" error={errors.free_text}>
                <textarea rows={3} className={inputClass} value={form.free_text ?? ''} onChange={(e) => set('free_text', e.target.value)} />
              </Field>
            </>
          )}
        </div>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        {step > 0 && <SecondaryButton onClick={() => setStep((s) => s - 1)}>← 前へ</SecondaryButton>}
        {step < steps.length - 1 && <PrimaryButton onClick={() => setStep((s) => s + 1)}>次へ →</PrimaryButton>}
        {step === steps.length - 1 && (
          <PrimaryButton onClick={() => save(false)} disabled={saving}>
            {saving ? '送信中…' : '✅ 送信する'}
          </PrimaryButton>
        )}
        <SecondaryButton onClick={() => save(true)} disabled={saving} className="ml-auto">
          💾 下書き保存
        </SecondaryButton>
      </div>
    </div>
  )
}
