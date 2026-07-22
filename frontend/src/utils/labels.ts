import type { PlanStatus, StressStatus, Urgency } from '../types'

export const stressLabels: Record<StressStatus, { label: string; icon: string; className: string }> = {
  low: { label: '低い', icon: '😊', className: 'bg-brand-leaf-soft text-emerald-800' },
  normal: { label: '標準', icon: '🙂', className: 'bg-sky-100 text-sky-800' },
  elevated: { label: 'やや高い', icon: '😐', className: 'bg-amber-100 text-amber-800' },
  high: { label: '高い', icon: '⚠️', className: 'bg-rose-100 text-rose-800' },
}

export const urgencyLabels: Record<Urgency, { label: string; className: string }> = {
  normal: { label: '通常', className: 'bg-paper-deep text-ink' },
  caution: { label: '注意', className: 'bg-amber-100 text-amber-800' },
  check: { label: '要確認', className: 'bg-orange-100 text-orange-800' },
  urgent: { label: '至急', className: 'bg-rose-600 text-white' },
}

export const planStatusLabels: Record<PlanStatus, { label: string; className: string }> = {
  draft: { label: '下書き', className: 'bg-paper-deep text-ink' },
  in_review: { label: 'スタッフ確認中', className: 'bg-amber-100 text-amber-800' },
  approved: { label: '承認済み', className: 'bg-brand-leaf-soft text-emerald-800' },
  active: { label: '実施中', className: 'bg-sky-100 text-sky-800' },
  evaluated: { label: '評価済み', className: 'bg-violet-100 text-violet-800' },
  closed: { label: '終了', className: 'bg-paper-deep text-ink-soft' },
}

export const goalStatusLabels: Record<string, { label: string; className: string }> = {
  active: { label: '取り組み中', className: 'bg-sky-100 text-sky-800' },
  achieved: { label: '達成', className: 'bg-brand-leaf-soft text-emerald-800' },
  paused: { label: '休止中', className: 'bg-amber-100 text-amber-800' },
  closed: { label: '終了', className: 'bg-paper-deep text-ink-soft' },
}

export const priorityLabels: Record<string, { label: string; className: string }> = {
  low: { label: '優先度: 低', className: 'bg-paper-deep text-ink' },
  medium: { label: '優先度: 中', className: 'bg-amber-100 text-amber-800' },
  high: { label: '優先度: 高', className: 'bg-rose-100 text-rose-800' },
}

export const alertTypeLabels: Record<string, string> = {
  stress_high_streak: 'ストレス高値の継続',
  mood_low_streak: '気分低下の継続',
  sleep_critical: '極端な睡眠不足',
  staff_urgent: 'スタッフ日報（至急）',
  risky_expression: '要確認の表現',
  report_gap: '日報の途切れ',
  score_drop: 'スコアの急低下',
}

export const mealLabels: Record<string, string> = {
  eaten: '食べた',
  partial: '少し食べた',
  skipped: '食べていない',
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso ?? '-'
  return `${formatDate(iso)} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export function todayISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function shortDate(iso: string): string {
  const parts = iso.split('-')
  return parts.length === 3 ? `${Number(parts[1])}/${Number(parts[2])}` : iso
}
