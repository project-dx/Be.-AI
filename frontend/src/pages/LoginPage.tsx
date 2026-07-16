import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import { loginSchema, type LoginForm } from '../schemas/forms'
import { useAuth } from '../stores/AuthContext'
import { errorMessage } from '../services/api'
import { Field, inputClass, PrimaryButton } from '../components/form'
import { ErrorMessage } from '../components/ui'
import { Logo } from '../components/Logo'

const SAVED_LOGIN_KEY = 'becolorful_saved_login'

function loadSavedLogin(): { email: string; password: string } | null {
  try {
    const raw = localStorage.getItem(SAVED_LOGIN_KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (typeof data?.email === 'string' && typeof data?.password === 'string') {
      return { email: data.email, password: data.password }
    }
  } catch {
    // 壊れたデータは無視して削除
    localStorage.removeItem(SAVED_LOGIN_KEY)
  }
  return null
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)
  const saved = loadSavedLogin()
  const [remember, setRemember] = useState(saved != null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: saved ?? { email: '', password: '' },
  })

  const onSubmit = async (values: LoginForm) => {
    setServerError(null)
    try {
      await login(values.email, values.password)
      // ログイン成功時のみ保存（チェックを外していたら削除）
      if (remember) {
        localStorage.setItem(SAVED_LOGIN_KEY, JSON.stringify(values))
      } else {
        localStorage.removeItem(SAVED_LOGIN_KEY)
      }
      navigate('/dashboard')
    } catch (err) {
      setServerError(errorMessage(err))
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="flex justify-center">
            <Logo className="h-14" />
          </h1>
          <p className="text-sm text-slate-500 mt-3">Well-being個別支援AI</p>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4 rounded-2xl bg-white border border-slate-200 p-6 shadow-sm"
          noValidate
        >
          <ErrorMessage message={serverError} />
          <Field label="メールアドレス" required error={errors.email?.message}>
            <input type="email" autoComplete="email" className={inputClass} {...register('email')} />
          </Field>
          <Field label="パスワード" required error={errors.password?.message}>
            <input type="password" autoComplete="current-password" className={inputClass} {...register('password')} />
          </Field>
          <div>
            <label className="flex items-start gap-2.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="mt-0.5 h-5 w-5 rounded border-slate-300 accent-emerald-600"
              />
              <span>
                <span className="block text-sm font-bold text-slate-700">次回から入力を省略する</span>
                <span className="block text-xs text-slate-400 mt-0.5">
                  メールアドレスとパスワードをこの端末に保存します。ほかの人も使う端末ではチェックしないでください
                </span>
              </span>
            </label>
          </div>
          <PrimaryButton type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? 'ログイン中…' : 'ログイン'}
          </PrimaryButton>
        </form>
        <p className="mt-4 text-center text-xs text-slate-400">
          本システムのAI出力は医療診断ではなく、支援判断を補助する参考情報です
        </p>
      </div>
    </div>
  )
}
