import { z } from 'zod'

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'メールアドレスを入力してください')
    .email('メールアドレスの形式が正しくありません'),
  password: z.string().min(1, 'パスワードを入力してください'),
})
export type LoginForm = z.infer<typeof loginSchema>

const timePattern = /^([01]?\d|2[0-3]):[0-5]\d$/

// 注意: union は先頭から評価されるため、空文字・null を数値より先に置く
// （z.coerce.number() は '' を 0 に変換してしまうため）
const optionalScale = z
  .union([z.literal(''), z.null(), z.coerce.number().int('整数で入力してください').min(1, '1〜5で選択してください').max(5, '1〜5で選択してください')])
  .transform((v) => (v === '' || v == null ? null : v))

const optionalMinutes = z
  .union([z.literal(''), z.null(), z.coerce.number().min(0, '0以上で入力してください').max(1440, '1440分以内で入力してください')])
  .transform((v) => (v === '' || v == null ? null : v))

export const dailyReportSchema = z.object({
  report_date: z.string().min(1, '日付を入力してください'),
  mood: optionalScale,
  sleep_hours: z
    .union([z.literal(''), z.null(), z.coerce.number().min(0, '0以上で入力してください').max(24, '24時間以内で入力してください')])
    .transform((v) => (v === '' || v == null ? null : v)),
  bedtime: z
    .union([z.string().regex(timePattern, '時刻は「23:00」の形式で入力してください'), z.literal('')])
    .transform((v) => (v === '' ? null : v)),
  wake_time: z
    .union([z.string().regex(timePattern, '時刻は「06:30」の形式で入力してください'), z.literal('')])
    .transform((v) => (v === '' ? null : v)),
  sleep_quality: optionalScale,
  breakfast_status: z.union([z.enum(['eaten', 'partial', 'skipped']), z.literal('')]).transform((v) => (v === '' ? null : v)),
  lunch_status: z.union([z.enum(['eaten', 'partial', 'skipped']), z.literal('')]).transform((v) => (v === '' ? null : v)),
  dinner_status: z.union([z.enum(['eaten', 'partial', 'skipped']), z.literal('')]).transform((v) => (v === '' ? null : v)),
  exercise_minutes: optionalMinutes,
  work_study_minutes: optionalMinutes,
  stress_level: optionalScale,
  fatigue_level: optionalScale,
  social_level: optionalScale,
  achievement: z.string().max(2000, '2000文字以内で入力してください').optional(),
  success_experience: z.string().max(2000, '2000文字以内で入力してください').optional(),
  difficulty: z.string().max(2000, '2000文字以内で入力してください').optional(),
  tomorrow_goal: z.string().max(2000, '2000文字以内で入力してください').optional(),
  free_text: z.string().max(4000, '4000文字以内で入力してください').optional(),
})
/** フォーム状態の型（zodの入力型はcoerceで崩れるため明示定義） */
export interface DailyReportForm {
  report_date: string
  mood: number | null
  sleep_hours: number | '' | null
  bedtime: string | null
  wake_time: string | null
  sleep_quality: number | null
  breakfast_status: 'eaten' | 'partial' | 'skipped' | '' | null
  lunch_status: 'eaten' | 'partial' | 'skipped' | '' | null
  dinner_status: 'eaten' | 'partial' | 'skipped' | '' | null
  exercise_minutes: number | '' | null
  work_study_minutes: number | '' | null
  stress_level: number | null
  fatigue_level: number | null
  social_level: number | null
  achievement: string
  success_experience: string
  difficulty: string
  tomorrow_goal: string
  free_text: string
}
export type DailyReportPayload = z.output<typeof dailyReportSchema>

/** 確定時に必須の項目（下書きは未入力可） */
export const requiredOnSubmit: { key: keyof DailyReportPayload; label: string }[] = [
  { key: 'mood', label: '今日の気分' },
  { key: 'sleep_hours', label: '睡眠時間' },
  { key: 'sleep_quality', label: '睡眠の質' },
  { key: 'stress_level', label: 'ストレス' },
  { key: 'fatigue_level', label: '疲労度' },
  { key: 'social_level', label: '人との交流' },
]

export const staffReportSchema = z.object({
  report_date: z.string().min(1, '記録日を入力してください'),
  support_minutes: optionalMinutes,
  support_content: z.string().min(1, '支援内容を入力してください').max(4000),
  user_condition: z.string().max(4000).optional(),
  conversation_summary: z.string().max(4000).optional(),
  positive_points: z.string().max(4000).optional(),
  issues: z.string().max(4000).optional(),
  behavior_changes: z.string().max(4000).optional(),
  support_method: z.string().max(4000).optional(),
  user_response: z.string().max(4000).optional(),
  next_check: z.string().max(4000).optional(),
  urgency: z.enum(['normal', 'caution', 'check', 'urgent']),
  free_text: z.string().max(4000).optional(),
})
export type StaffReportForm = z.input<typeof staffReportSchema>

export const goalSchema = z.object({
  title: z.string().min(1, '目標を入力してください').max(200, '200文字以内で入力してください'),
  description: z.string().max(2000).optional(),
  target_date: z.string().optional(),
})
export type GoalForm = z.infer<typeof goalSchema>

export const accountSchema = z.object({
  email: z.string().min(1, 'メールアドレスを入力してください').email('メールアドレスの形式が正しくありません'),
  password: z.string().min(8, 'パスワードは8文字以上で入力してください').max(72),
  role: z.enum(['admin', 'staff', 'user']),
  display_name: z.string().min(1, '表示名を入力してください').max(100),
  assigned_staff_id: z.union([z.coerce.number(), z.literal('')]).transform((v) => (v === '' ? null : v)),
})
export type AccountForm = z.input<typeof accountSchema>
