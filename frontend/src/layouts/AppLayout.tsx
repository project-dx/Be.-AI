import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../stores/AuthContext'
import { Logo } from '../components/Logo'

interface NavItem {
  to: string
  label: string
  icon: string
}

const navByRole: Record<string, NavItem[]> = {
  admin: [
    { to: '/dashboard', label: 'ダッシュボード', icon: '🏠' },
    { to: '/users', label: '利用者一覧', icon: '👥' },
    { to: '/risk-alerts', label: 'リスクアラート', icon: '🔔' },
    { to: '/accounts', label: 'アカウント管理', icon: '🗝️' },
    { to: '/audit-logs', label: '監査ログ', icon: '📋' },
    { to: '/settings', label: '設定', icon: '⚙️' },
  ],
  staff: [
    { to: '/dashboard', label: 'ダッシュボード', icon: '🏠' },
    { to: '/users', label: '担当利用者', icon: '👥' },
    { to: '/risk-alerts', label: 'リスクアラート', icon: '🔔' },
  ],
  user: [
    { to: '/dashboard', label: 'ホーム', icon: '🏠' },
    { to: '/daily-report', label: '今日の日報', icon: '📝' },
    { to: '/my-reports', label: 'ふりかえり', icon: '📖' },
    { to: '/goals', label: 'もくひょう', icon: '🎯' },
  ],
}

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const items = navByRole[user?.role ?? 'user'] ?? []

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const displayName = user?.profile?.display_name ?? user?.email ?? ''

  return (
    <div className="min-h-screen lg:flex">
      {/* サイドバー（PC） */}
      <aside className="hidden lg:flex lg:w-60 lg:flex-col lg:fixed lg:inset-y-0 bg-white border-r border-slate-200">
        <div className="px-5 py-5 border-b border-slate-100">
          <Logo className="h-9" />
          <p className="text-xs text-slate-500 mt-2">Well-being個別支援AI</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1" aria-label="メインメニュー">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? 'bg-emerald-100 text-emerald-900' : 'text-slate-600 hover:bg-slate-50'
                }`
              }
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-slate-100">
          <p className="text-sm font-bold text-slate-700 truncate">{displayName}</p>
          <p className="text-xs text-slate-400 mb-2">
            {user?.role === 'admin' ? '管理者' : user?.role === 'staff' ? 'スタッフ' : '利用者'}
          </p>
          <button
            onClick={handleLogout}
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
          >
            ログアウト
          </button>
        </div>
      </aside>

      {/* ヘッダー（モバイル） */}
      <div className="lg:hidden sticky top-0 z-20 flex items-center justify-between bg-white border-b border-slate-200 px-4 py-3">
        <Logo className="h-7" />
        <button
          onClick={() => setMenuOpen((v) => !v)}
          aria-expanded={menuOpen}
          aria-label="メニューを開く"
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
        >
          ☰ メニュー
        </button>
      </div>
      {menuOpen && (
        <nav className="lg:hidden fixed inset-x-0 top-[53px] z-20 bg-white border-b border-slate-200 shadow-lg" aria-label="モバイルメニュー">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-5 py-3 text-sm border-b border-slate-50 ${
                  isActive ? 'bg-emerald-50 text-emerald-900 font-bold' : 'text-slate-700'
                }`
              }
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
          <button onClick={handleLogout} className="flex w-full items-center gap-3 px-5 py-3 text-sm text-slate-600">
            <span aria-hidden>🚪</span> ログアウト（{displayName}）
          </button>
        </nav>
      )}

      {/* メインコンテンツ */}
      <main className="flex-1 lg:ml-60 px-4 py-5 sm:px-6 lg:px-8 max-w-6xl w-full mx-auto">
        <Outlet />
      </main>
    </div>
  )
}
