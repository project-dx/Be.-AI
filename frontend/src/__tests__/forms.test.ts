import { describe, expect, it } from 'vitest'
import { dailyReportSchema, loginSchema, staffReportSchema } from '../schemas/forms'

describe('loginSchema', () => {
  it('未入力で日本語エラーを返す', () => {
    const result = loginSchema.safeParse({ email: '', password: '' })
    expect(result.success).toBe(false)
    if (!result.success) {
      const messages = result.error.issues.map((i) => i.message)
      expect(messages).toContain('メールアドレスを入力してください')
      expect(messages).toContain('パスワードを入力してください')
    }
  })

  it('不正なメール形式でエラー', () => {
    const result = loginSchema.safeParse({ email: 'abc', password: 'x' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('メールアドレスの形式が正しくありません')
    }
  })
})

describe('dailyReportSchema', () => {
  const base = {
    report_date: '2026-07-16',
    mood: 3,
    sleep_hours: 7,
    bedtime: '23:00',
    wake_time: '06:30',
    sleep_quality: 3,
    breakfast_status: 'eaten',
    lunch_status: '',
    dinner_status: '',
    exercise_minutes: 30,
    work_study_minutes: 240,
    stress_level: 2,
    fatigue_level: 2,
    social_level: 3,
  }

  it('正常な入力を受け付ける', () => {
    const result = dailyReportSchema.safeParse(base)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.lunch_status).toBeNull()
    }
  })

  it('気分の範囲外（6）を拒否する', () => {
    const result = dailyReportSchema.safeParse({ ...base, mood: 6 })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('1〜5で選択してください')
    }
  })

  it('睡眠時間25時間を拒否する', () => {
    const result = dailyReportSchema.safeParse({ ...base, sleep_hours: 25 })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('24時間以内で入力してください')
    }
  })

  it('睡眠時間0時間は境界値として受け付ける', () => {
    const result = dailyReportSchema.safeParse({ ...base, sleep_hours: 0 })
    expect(result.success).toBe(true)
  })

  it('時刻形式が不正な場合は日本語エラー', () => {
    const result = dailyReportSchema.safeParse({ ...base, bedtime: '25:99' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('形式で入力してください')
    }
  })

  it('未入力（空文字）はnullに変換される', () => {
    const result = dailyReportSchema.safeParse({ ...base, sleep_hours: '', mood: null })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.sleep_hours).toBeNull()
      expect(result.data.mood).toBeNull()
    }
  })
})

describe('staffReportSchema', () => {
  it('支援内容が必須', () => {
    const result = staffReportSchema.safeParse({
      report_date: '2026-07-16',
      support_content: '',
      urgency: 'normal',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues.some((i) => i.message === '支援内容を入力してください')).toBe(true)
    }
  })

  it('緊急度は4種類のみ', () => {
    const result = staffReportSchema.safeParse({
      report_date: '2026-07-16',
      support_content: '支援内容',
      urgency: 'critical',
    })
    expect(result.success).toBe(false)
  })
})
