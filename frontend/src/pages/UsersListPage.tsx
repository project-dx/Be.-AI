import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage, usersApi } from '../services/api'
import { Badge, Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { formatDate } from '../utils/labels'
import type { User } from '../types'

export default function UsersListPage() {
  const [users, setUsers] = useState<User[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  useEffect(() => {
    usersApi.list('user').then(setUsers).catch((e) => setError(errorMessage(e)))
  }, [])

  if (error) return <ErrorMessage message={error} />
  if (!users) return <Loading />

  const filtered = users.filter(
    (u) =>
      !query ||
      (u.profile?.display_name ?? '').includes(query) ||
      u.email.toLowerCase().includes(query.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-slate-800">👥 利用者一覧</h1>
      <input
        type="search"
        placeholder="名前・メールアドレスで検索"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full max-w-sm rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-200"
        aria-label="利用者の検索"
      />
      {filtered.length === 0 ? (
        <EmptyState message="該当する利用者がいません" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((u) => (
            <Link key={u.id} to={`/users/${u.id}`}>
              <Card className="hover:border-emerald-300 transition-colors h-full">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-emerald-100 text-lg" aria-hidden>
                    🙂
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-slate-800 truncate">{u.profile?.display_name ?? u.email}</p>
                    <p className="text-xs text-slate-400 truncate">{u.email}</p>
                  </div>
                  {!u.is_active && <Badge label="無効" className="bg-slate-200 text-slate-600 ml-auto" />}
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  支援開始日: {formatDate(u.profile?.support_start_date)}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
