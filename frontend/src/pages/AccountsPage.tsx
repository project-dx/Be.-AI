import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { errorMessage, usersApi } from '../services/api'
import { accountSchema, type AccountForm } from '../schemas/forms'
import { Field, inputClass, PrimaryButton } from '../components/form'
import { Badge, Card, ErrorMessage, Loading } from '../components/ui'
import type { User } from '../types'

const roleLabels: Record<string, { label: string; className: string }> = {
  admin: { label: '管理者', className: 'bg-violet-100 text-violet-800' },
  staff: { label: 'スタッフ', className: 'bg-sky-100 text-sky-800' },
  user: { label: '利用者', className: 'bg-emerald-100 text-emerald-800' },
}

export default function AccountsPage() {
  const [users, setUsers] = useState<User[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(() => {
    usersApi.list().then(setUsers).catch((e) => setError(errorMessage(e)))
  }, [])

  useEffect(load, [load])

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AccountForm>({
    resolver: zodResolver(accountSchema),
    defaultValues: { role: 'user', assigned_staff_id: '' },
  })

  const onSubmit = async (values: AccountForm) => {
    setError(null)
    setMessage(null)
    try {
      await usersApi.create({
        email: values.email,
        password: values.password,
        role: values.role,
        profile: {
          display_name: values.display_name,
          assigned_staff_id:
            values.role === 'user' && values.assigned_staff_id !== '' ? Number(values.assigned_staff_id) : null,
        },
      })
      setMessage('アカウントを作成しました')
      reset({ role: 'user', assigned_staff_id: '', email: '', password: '', display_name: '' })
      load()
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  const toggleActive = async (u: User) => {
    const verb = u.is_active ? '無効化' : '有効化'
    if (!window.confirm(`${u.profile?.display_name ?? u.email} を${verb}しますか？`)) return
    try {
      await usersApi.update(u.id, { is_active: !u.is_active })
      load()
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  if (!users) return <Loading />
  const staffList = users.filter((u) => u.role === 'staff' && u.is_active)
  const role = watch('role')

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-slate-800">🗝️ アカウント管理</h1>
      <ErrorMessage message={error} />
      {message && (
        <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          ✅ {message}
        </p>
      )}

      <Card title="➕ 新規アカウント作成">
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="メールアドレス" required error={errors.email?.message}>
            <input type="email" className={inputClass} {...register('email')} />
          </Field>
          <Field label="パスワード" required error={errors.password?.message} hint="8文字以上">
            <input type="password" autoComplete="new-password" className={inputClass} {...register('password')} />
          </Field>
          <Field label="表示名" required error={errors.display_name?.message}>
            <input className={inputClass} {...register('display_name')} />
          </Field>
          <Field label="ロール" required error={errors.role?.message}>
            <select className={inputClass} {...register('role')}>
              <option value="user">利用者</option>
              <option value="staff">スタッフ</option>
              <option value="admin">管理者</option>
            </select>
          </Field>
          {role === 'user' && (
            <Field label="担当スタッフ" error={errors.assigned_staff_id?.message}>
              <select className={inputClass} {...register('assigned_staff_id')}>
                <option value="">（未割り当て）</option>
                {staffList.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.profile?.display_name ?? s.email}
                  </option>
                ))}
              </select>
            </Field>
          )}
          <div className="sm:col-span-2">
            <PrimaryButton type="submit" disabled={isSubmitting}>作成する</PrimaryButton>
          </div>
        </form>
      </Card>

      <Card title="👥 アカウント一覧">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-400">
                <th className="py-2 pr-3 font-bold">表示名</th>
                <th className="py-2 pr-3 font-bold">メール</th>
                <th className="py-2 pr-3 font-bold">ロール</th>
                <th className="py-2 pr-3 font-bold">状態</th>
                <th className="py-2 font-bold">操作</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const r = roleLabels[u.role]
                return (
                  <tr key={u.id} className="border-b border-slate-100">
                    <td className="py-2.5 pr-3 font-bold text-slate-700">{u.profile?.display_name ?? '-'}</td>
                    <td className="py-2.5 pr-3 text-slate-500">{u.email}</td>
                    <td className="py-2.5 pr-3"><Badge label={r.label} className={r.className} /></td>
                    <td className="py-2.5 pr-3">
                      <Badge
                        label={u.is_active ? '有効' : '無効'}
                        className={u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'}
                      />
                    </td>
                    <td className="py-2.5">
                      <button
                        onClick={() => toggleActive(u)}
                        className="rounded-lg border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
                      >
                        {u.is_active ? '無効化' : '有効化'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
