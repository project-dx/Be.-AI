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
    <div className="color-drops flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-7 rise-in">
          <h1 className="flex justify-center">
            <Logo className="h-14" />
          </h1>
          <p className="mt-3 text-[11px] font-bold tracking-[0.22em] text-ink-faint">
            WELL-BEING個別支援AI
          </p>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rise-in rise-in-1 relative space-y-4 overflow-hidden rounded-3xl bg-white border border-line p-7 shadow-pop"
          noValidate
        >
          <div className="rainbow-bar absolute inset-x-0 top-0 h-1.5" aria-hidden />
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
                className="mt-0.5 h-5 w-5 rounded border-line-strong accent-brand-leaf"
              />
              <span>
                <span className="block text-sm font-bold text-ink">次回から入力を省略する</span>
                <span className="block text-xs text-ink-faint mt-0.5">
                  メールアドレスとパスワードをこの端末に保存します。ほかの人も使う端末ではチェックしないでください
                </span>
              </span>
            </label>
          </div>
          <PrimaryButton type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? 'ログイン中…' : 'ログイン'}
          </PrimaryButton>
        </form>
        <p className="rise-in rise-in-2 mt-5 text-center text-xs text-ink-faint">
          本システムのAI出力は医療診断ではなく、支援判断を補助する参考情報です
        </p>
      </div>
    </div>
  )
}
