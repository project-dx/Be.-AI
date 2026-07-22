import { Link } from 'react-router-dom'

function ErrorShell({ icon, title, message }: { icon: string; title: string; message: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <p className="text-4xl" aria-hidden>{icon}</p>
      <h1 className="mt-3 text-xl font-bold text-ink">{title}</h1>
      <p className="mt-2 text-sm text-ink-soft">{message}</p>
      <Link
        to="/dashboard"
        className="mt-6 rounded-xl bg-brand-leaf px-5 py-2.5 text-sm font-bold text-white hover:brightness-105"
      >
        ホームへ戻る
      </Link>
    </div>
  )
}

export function NotFoundPage() {
  return (
    <ErrorShell
      icon="🔍"
      title="ページが見つかりません"
      message="お探しのページは存在しないか、移動した可能性があります。"
    />
  )
}

export function ForbiddenPage() {
  return (
    <ErrorShell
      icon="🔒"
      title="アクセス権限がありません"
      message="このページを表示する権限がありません。必要な場合は管理者へお問い合わせください。"
    />
  )
}
