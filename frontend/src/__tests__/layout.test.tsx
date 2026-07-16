import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import type { User } from '../types'

const mockUseAuth = vi.fn()

vi.mock('../stores/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

import AppLayout from '../layouts/AppLayout'

function makeUser(role: User['role']): User {
  return {
    id: 1,
    email: 'test@example.com',
    role,
    is_active: true,
    created_at: '2026-01-01T00:00:00',
    profile: {
      id: 1,
      user_id: 1,
      display_name: 'テスト太郎',
      date_of_birth: null,
      support_start_date: null,
      assigned_staff_id: null,
      notes: null,
    },
  }
}

function renderLayout(role: User['role']) {
  mockUseAuth.mockReturnValue({ user: makeUser(role), loading: false, login: vi.fn(), logout: vi.fn() })
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<div>コンテンツ</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('AppLayout ロール別メニュー', () => {
  beforeEach(() => mockUseAuth.mockReset())

  it('管理者には監査ログ・アカウント管理・設定メニューを表示する', () => {
    renderLayout('admin')
    expect(screen.getByRole('link', { name: /監査ログ/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /アカウント管理/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /設定/ })).toBeInTheDocument()
    expect(screen.getByText('管理者')).toBeInTheDocument()
  })

  it('スタッフには管理者専用メニューを表示しない', () => {
    renderLayout('staff')
    expect(screen.getByRole('link', { name: /担当利用者/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /監査ログ/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /アカウント管理/ })).not.toBeInTheDocument()
  })

  it('利用者には日報・ふりかえり・目標メニューを表示する', () => {
    renderLayout('user')
    expect(screen.getByRole('link', { name: /今日の日報/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /ふりかえり/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /もくひょう/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /リスクアラート/ })).not.toBeInTheDocument()
  })
})
