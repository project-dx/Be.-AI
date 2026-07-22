import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { errorMessage, goalsApi } from '../services/api'
import { useAuth } from '../stores/AuthContext'
import { goalSchema, type GoalForm } from '../schemas/forms'
import { Field, inputClass, PrimaryButton } from '../components/form'
import { Badge, Card, EmptyState, ErrorMessage, Loading, ProgressBar } from '../components/ui'
import { formatDate, goalStatusLabels } from '../utils/labels'
import type { Goal } from '../types'

export default function GoalsPage({ targetUserId }: { targetUserId?: number }) {
  const { user } = useAuth()
  const userId = targetUserId ?? user?.id
  const [goals, setGoals] = useState<Goal[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    if (!userId) return
    goalsApi.list(userId).then(setGoals).catch((e) => setError(errorMessage(e)))
  }, [userId])

  useEffect(load, [load])

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GoalForm>({ resolver: zodResolver(goalSchema) })

  const onSubmit = async (values: GoalForm) => {
    if (!userId) return
    try {
      await goalsApi.create(userId, {
        title: values.title,
        description: values.description || null,
        target_date: values.target_date || null,
      })
      reset()
      load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  const updateProgress = async (goal: Goal, progress: number) => {
    try {
      await goalsApi.update(goal.id, { progress, status: progress >= 100 ? 'achieved' : goal.status })
      load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  if (error && !goals) return <ErrorMessage message={error} />
  if (!goals) return <Loading />

  return (
    <div className="space-y-4">
      {!targetUserId && <h1 className="text-xl font-bold text-ink">🎯 目標管理</h1>}
      <ErrorMessage message={error} />

      <Card title="新しい目標を登録">
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-3">
          <Field label="目標" required error={errors.title?.message} hint="小さくて達成できそうな目標がおすすめです">
            <input className={inputClass} placeholder="例: 週5日、日報を入力する" {...register('title')} />
          </Field>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="くわしい内容" error={errors.description?.message}>
              <input className={inputClass} {...register('description')} />
            </Field>
            <Field label="目標日" error={errors.target_date?.message}>
              <input type="date" className={inputClass} {...register('target_date')} />
            </Field>
          </div>
          <PrimaryButton type="submit" disabled={isSubmitting}>登録する</PrimaryButton>
        </form>
      </Card>

      {goals.length === 0 ? (
        <EmptyState message="まだ目標がありません。上のフォームから登録してみましょう" />
      ) : (
        <div className="space-y-3">
          {goals.map((g) => {
            const status = goalStatusLabels[g.status] ?? goalStatusLabels.active
            return (
              <Card key={g.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-bold text-ink">{g.title}</p>
                    {g.description && <p className="text-sm text-ink-soft mt-0.5">{g.description}</p>}
                    <p className="text-xs text-ink-faint mt-1">目標日: {formatDate(g.target_date)}</p>
                  </div>
                  <Badge label={status.label} className={status.className} />
                </div>
                <div className="mt-3">
                  <ProgressBar value={g.progress} label="進捗" />
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {[0, 25, 50, 75, 100].map((p) => (
                      <button
                        key={p}
                        onClick={() => updateProgress(g, p)}
                        className={`rounded-lg border px-2.5 py-1 text-xs ${
                          g.progress === p ? 'border-brand-leaf bg-brand-leaf-soft font-bold text-emerald-800' : 'border-line text-ink-soft hover:bg-paper'
                        }`}
                      >
                        {p}%
                      </button>
                    ))}
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
