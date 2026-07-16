import axios, { AxiosError } from 'axios'
import type {
  AdminDashboard,
  AiAnalysis,
  AuditLog,
  DailyReport,
  Goal,
  PlanVersion,
  RiskAlert,
  ScoreResult,
  StaffDashboard,
  StaffReport,
  SupportAction,
  SupportPlan,
  User,
  UserDashboard,
} from '../types'

const TOKEN_KEY = 'becolorful_access_token'
const REFRESH_KEY = 'becolorful_refresh_token'

export const tokenStore = {
  get access() {
    return localStorage.getItem(TOKEN_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(TOKEN_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing: Promise<string | null> | null = null

async function tryRefresh(): Promise<string | null> {
  const refresh = tokenStore.refresh
  if (!refresh) return null
  try {
    const { data } = await axios.post('/api/auth/refresh', { refresh_token: refresh })
    tokenStore.set(data.access_token)
    return data.access_token
  } catch {
    tokenStore.clear()
    return null
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config
    if (
      error.response?.status === 401 &&
      original &&
      !(original as { _retried?: boolean })._retried &&
      !original.url?.includes('/auth/')
    ) {
      ;(original as { _retried?: boolean })._retried = true
      refreshing = refreshing ?? tryRefresh()
      const token = await refreshing
      refreshing = null
      if (token) {
        original.headers.Authorization = `Bearer ${token}`
        return api.request(original)
      }
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

/** APIエラーから日本語メッセージを取り出す */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    if (typeof detail === 'string') return detail
    if (error.response?.status === 403) return 'この操作を行う権限がありません'
    if (!error.response) return 'サーバーへ接続できません。ネットワークを確認してください'
  }
  return 'エラーが発生しました。時間をおいて再度お試しください'
}

// --- 認証 ---
export const authApi = {
  async login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password })
    tokenStore.set(data.access_token, data.refresh_token)
    return data
  },
  me: () => api.get<User>('/auth/me').then((r) => r.data),
  logout() {
    tokenStore.clear()
  },
}

// --- 利用者・アカウント ---
export const usersApi = {
  list: (role?: string) =>
    api.get<User[]>('/users', { params: role ? { role } : {} }).then((r) => r.data),
  get: (id: number) => api.get<User>(`/users/${id}`).then((r) => r.data),
  create: (body: Record<string, unknown>) => api.post<User>('/users', body).then((r) => r.data),
  update: (id: number, body: Record<string, unknown>) =>
    api.patch<User>(`/users/${id}`, body).then((r) => r.data),
}

// --- 日報 ---
export const reportsApi = {
  list: (userId: number, params?: { from?: string; to?: string; limit?: number }) =>
    api.get<DailyReport[]>(`/users/${userId}/daily-reports`, { params }).then((r) => r.data),
  get: (userId: number, reportId: number) =>
    api.get<DailyReport>(`/users/${userId}/daily-reports/${reportId}`).then((r) => r.data),
  create: (userId: number, body: Record<string, unknown>) =>
    api.post<DailyReport>(`/users/${userId}/daily-reports`, body).then((r) => r.data),
  update: (userId: number, reportId: number, body: Record<string, unknown>) =>
    api.patch<DailyReport>(`/users/${userId}/daily-reports/${reportId}`, body).then((r) => r.data),
}

export const staffReportsApi = {
  list: (userId: number) =>
    api.get<StaffReport[]>(`/users/${userId}/staff-reports`).then((r) => r.data),
  create: (userId: number, body: Record<string, unknown>) =>
    api.post<StaffReport>(`/users/${userId}/staff-reports`, body).then((r) => r.data),
  update: (userId: number, reportId: number, body: Record<string, unknown>) =>
    api.patch<StaffReport>(`/users/${userId}/staff-reports/${reportId}`, body).then((r) => r.data),
}

// --- スコア ---
export const scoresApi = {
  list: (userId: number, params?: { from?: string; to?: string }) =>
    api.get<ScoreResult[]>(`/users/${userId}/scores`, { params }).then((r) => r.data),
  recalculate: (userId: number, days = 30) =>
    api.post(`/users/${userId}/scores/recalculate`, { days }).then((r) => r.data),
}

// --- AI分析 ---
export const analysesApi = {
  list: (userId: number) =>
    api.get<AiAnalysis[]>(`/users/${userId}/ai-analyses`).then((r) => r.data),
  get: (userId: number, analysisId: number) =>
    api.get<AiAnalysis>(`/users/${userId}/ai-analyses/${analysisId}`).then((r) => r.data),
  run: (userId: number, periodDays = 14) =>
    api
      .post<AiAnalysis>(`/users/${userId}/ai-analyses`, {
        analysis_type: 'daily_analysis',
        period_days: periodDays,
      })
      .then((r) => r.data),
}

// --- 個別支援計画 ---
export const plansApi = {
  list: (userId: number) =>
    api.get<SupportPlan[]>(`/users/${userId}/support-plans`).then((r) => r.data),
  generate: (userId: number) =>
    api.post<SupportPlan>(`/users/${userId}/support-plans/generate`).then((r) => r.data),
  update: (planId: number, body: Record<string, unknown>) =>
    api.patch<SupportPlan>(`/support-plans/${planId}`, body).then((r) => r.data),
  approve: (planId: number) =>
    api.post<SupportPlan>(`/support-plans/${planId}/approve`).then((r) => r.data),
  versions: (planId: number) =>
    api.get<PlanVersion[]>(`/support-plans/${planId}/versions`).then((r) => r.data),
}

export const actionsApi = {
  list: (userId: number) =>
    api.get<SupportAction[]>(`/users/${userId}/support-actions`).then((r) => r.data),
  create: (userId: number, body: Record<string, unknown>) =>
    api.post<SupportAction>(`/users/${userId}/support-actions`, body).then((r) => r.data),
}

// --- 目標 ---
export const goalsApi = {
  list: (userId: number) => api.get<Goal[]>(`/users/${userId}/goals`).then((r) => r.data),
  create: (userId: number, body: Record<string, unknown>) =>
    api.post<Goal>(`/users/${userId}/goals`, body).then((r) => r.data),
  update: (goalId: number, body: Record<string, unknown>) =>
    api.patch<Goal>(`/goals/${goalId}`, body).then((r) => r.data),
}

// --- リスク ---
export const risksApi = {
  list: (status?: 'open' | 'acknowledged') =>
    api.get<RiskAlert[]>('/risk-alerts', { params: status ? { status } : {} }).then((r) => r.data),
  acknowledge: (id: number) =>
    api.post<RiskAlert>(`/risk-alerts/${id}/acknowledge`).then((r) => r.data),
}

// --- ダッシュボード ---
export const dashboardApi = {
  user: () => api.get<UserDashboard>('/dashboard/user').then((r) => r.data),
  staff: () => api.get<StaffDashboard>('/dashboard/staff').then((r) => r.data),
  admin: () => api.get<AdminDashboard>('/dashboard/admin').then((r) => r.data),
  forUser: (userId: number) =>
    api.get<UserDashboard>(`/users/${userId}/dashboard`).then((r) => r.data),
}

// --- 監査ログ・設定 ---
export const auditApi = {
  list: (params?: { action?: string; from?: string; to?: string; limit?: number }) =>
    api.get<AuditLog[]>('/audit-logs', { params }).then((r) => r.data),
}

export const settingsApi = {
  getScoringWeights: () =>
    api
      .get<{ weights: Record<string, Record<string, number>>; defaults: Record<string, Record<string, number>> }>(
        '/settings/scoring-weights',
      )
      .then((r) => r.data),
  updateScoringWeights: (weights: Record<string, Record<string, number>>) =>
    api.put('/settings/scoring-weights', { weights }).then((r) => r.data),
}
