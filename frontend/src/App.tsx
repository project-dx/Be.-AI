import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AuthProvider, useAuth } from './stores/AuthContext'
import AppLayout from './layouts/AppLayout'
import LoginPage from './pages/LoginPage'
import UserDashboardPage from './pages/UserDashboardPage'
import StaffDashboardPage from './pages/StaffDashboardPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import UsersListPage from './pages/UsersListPage'
import UserDetailPage from './pages/UserDetailPage'
import DailyReportFormPage from './pages/DailyReportFormPage'
import StaffReportFormPage from './pages/StaffReportFormPage'
import MyReportsPage from './pages/MyReportsPage'
import GoalsPage from './pages/GoalsPage'
import RiskAlertsPage from './pages/RiskAlertsPage'
import AccountsPage from './pages/AccountsPage'
import AuditLogsPage from './pages/AuditLogsPage'
import SettingsPage from './pages/SettingsPage'
import { ForbiddenPage, NotFoundPage } from './pages/ErrorPages'
import { Loading } from './components/ui'
import type { Role } from './types'

function RequireAuth({ children, roles }: { children: ReactNode; roles?: Role[] }) {
  const { user, loading } = useAuth()
  if (loading) return <Loading label="読み込み中…" />
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <ForbiddenPage />
  return <>{children}</>
}

function DashboardByRole() {
  const { user } = useAuth()
  if (user?.role === 'admin') return <AdminDashboardPage />
  if (user?.role === 'staff') return <StaffDashboardPage />
  return <UserDashboardPage />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <RequireAuth>
                <AppLayout />
              </RequireAuth>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardByRole />} />

            {/* 利用者向け */}
            <Route
              path="/daily-report"
              element={
                <RequireAuth roles={['user']}>
                  <DailyReportFormPage />
                </RequireAuth>
              }
            />
            <Route
              path="/my-reports"
              element={
                <RequireAuth roles={['user']}>
                  <MyReportsPage />
                </RequireAuth>
              }
            />
            <Route
              path="/goals"
              element={
                <RequireAuth roles={['user']}>
                  <GoalsPage />
                </RequireAuth>
              }
            />

            {/* スタッフ・管理者向け */}
            <Route
              path="/users"
              element={
                <RequireAuth roles={['staff', 'admin']}>
                  <UsersListPage />
                </RequireAuth>
              }
            />
            <Route
              path="/users/:userId"
              element={
                <RequireAuth roles={['staff', 'admin']}>
                  <UserDetailPage />
                </RequireAuth>
              }
            />
            <Route
              path="/users/:userId/staff-report/new"
              element={
                <RequireAuth roles={['staff', 'admin']}>
                  <StaffReportFormPage />
                </RequireAuth>
              }
            />
            <Route
              path="/risk-alerts"
              element={
                <RequireAuth roles={['staff', 'admin']}>
                  <RiskAlertsPage />
                </RequireAuth>
              }
            />

            {/* 管理者向け */}
            <Route
              path="/accounts"
              element={
                <RequireAuth roles={['admin']}>
                  <AccountsPage />
                </RequireAuth>
              }
            />
            <Route
              path="/audit-logs"
              element={
                <RequireAuth roles={['admin']}>
                  <AuditLogsPage />
                </RequireAuth>
              }
            />
            <Route
              path="/settings"
              element={
                <RequireAuth roles={['admin']}>
                  <SettingsPage />
                </RequireAuth>
              }
            />

            <Route path="/403" element={<ForbiddenPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
