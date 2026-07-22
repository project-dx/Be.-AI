import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../stores/AuthContext'
import { Logo } from '../components/Logo'

interface NavItem {
  to: string
  label: string
  icon: string
  /** アクティブ時の色（Be.カラフルのブランドカラーを1項目ずつ） */
  activeClass: string
  dotClass: string
}

const navByRole: Record<string, NavItem[]> = {
  admin: [
    { to: '/dashboard', label: 'ダッシュボード', icon: '🏠', activeClass: 'bg-brand-pink-soft text-ink', dotClass: 'bg-brand-pink' },
    { to: '/users', label: '利用者一覧', icon: '👥', activeClass: 'bg-brand-coral-soft text-ink', dotClass: 'bg-brand-coral' },
    { to: '/risk-alerts', label: 'リスクアラート', icon: '🔔', activeClass: 'bg-brand-sun-soft text-ink', dotClass: 'bg-brand-sun' },
    { to: '/accounts', label: 'アカウント管理', icon: '🗝️', activeClass: 'bg-brand-leaf-soft text-ink', dotClass: 'bg-brand-leaf' },
    { to: '/audit-logs', label: '監査ログ', icon: '📋', activeClass: 'bg-brand-sea-soft text-ink', dotClass: 'bg-brand-sea' },
    { to: '/settings', label: '設定', icon: '⚙️', activeClass: 'bg-brand-plum-soft text-ink', dotClass: 'bg-brand-plum' },
  ],
  staff: [
    { to: '/dashboard', label: 'ダッシュボード', icon: '🏠', activeClass: 'bg-brand-pink-soft text-ink', dotClass: 'bg-brand-pink' },
    { to: '/users', label: '担当利用者', icon: '👥', activeClass: 'bg-brand-coral-soft text-ink', dotClass: 'bg-brand-coral' },
    { to: '/risk-alerts', label: 'リスクアラート', icon: '🔔', activeClass: 'bg-brand-sun-soft text-ink', dotClass: 'bg-brand-sun' },
  ],
  user: [
    { to: '/dashboard', label: 'ホーム', icon: '🏠', activeClass: 'bg-brand-pink-soft text-ink', dotClass: 'bg-brand-pink' },
    { to: '/daily-report', label: '今日の日報', icon: '📝', activeClass: 'bg-brand-sun-soft text-ink', dotClass: 'bg-brand-sun' },
    { to: '/my-reports', label: 'ふりかえり', icon: '📖', activeClass: 'bg-brand-leaf-soft text-ink', dotClass: 'bg-brand-leaf' },
    { to: '/goals', label: 'もくひょう', icon: '🎯', activeClass: 'bg-brand-sea-soft text-ink', dotClass: 'bg-brand-sea' },
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
  const roleLabel = user?.role === 'admin' ? '管理者' : user?.role === 'staff' ? 'スタッフ' : '利用者'

  return (
    <div className="min-h-screen lg:flex">
      {/* サイドバー（PC） */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 bg-white border-r border-line">
        {/* ブランドのしるし: レインボーの帯 */}
        <div className="rainbow-bar h-1.5 shrink-0" aria-hidden />
        <div className="px-6 pt-6 pb-5">
          <Logo className="h-10" />
          <p className="mt-2.5 text-[11px] font-bold tracking-[0.14em] text-ink-faint">
            WELL-BEING個別支援AI
          </p>
        </div>
        <nav className="flex-1 px-3.5 py-2 space-y-1" aria-label="メインメニュー">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-2xl px-3.5 py-2.5 text-sm font-bold transition-all ${
                  isActive
                    ? item.activeClass
                    : 'text-ink-soft hover:bg-paper hover:translate-x-0.5'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    aria-hidden
                    className={`h-2 w-2 shrink-0 rounded-full transition-all ${
                      isActive ? item.dotClass : 'bg-line-strong group-hover:bg-ink-faint'
                    }`}
                  />
                  <span aria-hidden className="text-base leading-none">{item.icon}</span>
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="mx-4 mb-4 rounded-2xl bg-paper px-4 py-3.5">
          <p className="text-sm font-bold text-ink truncate">{displayName}</p>
          <p className="text-xs text-ink-faint mb-2.5">{roleLabel}</p>
          <button
            onClick={handleLogout}
            className="w-full rounded-xl border border-line-strong bg-white px-3 py-2 text-xs font-bold text-ink-soft transition-colors hover:bg-paper-deep"
          >
            ログアウト
          </button>
        </div>
      </aside>

      {/* ヘッダー（モバイル） */}
      <div className="lg:hidden sticky top-0 z-20 bg-white border-b border-line">
        <div className="rainbow-bar h-1" aria-hidden />
        <div className="flex items-center justify-between px-4 py-3">
          <Logo className="h-7" />
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-expanded={menuOpen}
            aria-label="メニューを開く"
            className="rounded-xl border border-line-strong px-3.5 py-1.5 text-sm font-bold text-ink-soft"
          >
            ☰ メニュー
          </button>
        </div>
      </div>
      {menuOpen && (
        <nav className="lg:hidden fixed inset-x-0 top-[57px] z-20 bg-white border-b border-line shadow-pop rounded-b-3xl overflow-hidden" aria-label="モバイルメニュー">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-5 py-3.5 text-sm border-b border-paper-deep ${
                  isActive ? `${item.activeClass} font-bold` : 'text-ink-soft'
                }`
              }
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
          <button onClick={handleLogout} className="flex w-full items-center gap-3 px-5 py-3.5 text-sm text-ink-soft">
            <span aria-hidden>🚪</span> ログアウト（{displayName}）
          </button>
        </nav>
      )}

      {/* メインコンテンツ */}
      <main className="flex-1 lg:ml-64 px-4 py-6 sm:px-6 lg:px-10 max-w-6xl w-full mx-auto">
        <Outlet />
      </main>
    </div>
  )
}
