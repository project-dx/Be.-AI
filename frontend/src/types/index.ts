export type Role = 'admin' | 'staff' | 'user'

export interface Profile {
  id: number
  user_id: number
  display_name: string
  date_of_birth: string | null
  support_start_date: string | null
  assigned_staff_id: number | null
  notes: string | null
}

export interface User {
  id: number
  email: string
  role: Role
  is_active: boolean
  created_at: string
  profile: Profile | null
}

export type MealStatus = 'eaten' | 'partial' | 'skipped'
export type Urgency = 'normal' | 'caution' | 'check' | 'urgent'

export interface DailyReport {
  id: number
  user_id: number
  report_date: string
  mood: number | null
  sleep_hours: number | null
  bedtime: string | null
  wake_time: string | null
  sleep_quality: number | null
  breakfast_status: MealStatus | null
  lunch_status: MealStatus | null
  dinner_status: MealStatus | null
  exercise_minutes: number | null
  work_study_minutes: number | null
  stress_level: number | null
  fatigue_level: number | null
  social_level: number | null
  achievement: string | null
  success_experience: string | null
  difficulty: string | null
  tomorrow_goal: string | null
  free_text: string | null
  is_draft: boolean
  created_at: string
  updated_at: string
}

export interface StaffReport {
  id: number
  user_id: number
  staff_id: number
  staff_name: string | null
  report_date: string
  support_minutes: number | null
  support_content: string | null
  user_condition: string | null
  conversation_summary: string | null
  positive_points: string | null
  issues: string | null
  behavior_changes: string | null
  support_method: string | null
  user_response: string | null
  next_check: string | null
  urgency: Urgency
  free_text: string | null
  created_at: string
}

export type StressStatus = 'low' | 'normal' | 'elevated' | 'high'

export interface ScoreResult {
  id: number
  user_id: number
  score_date: string
  life_rhythm_score: number | null
  sleep_score: number | null
  mental_score: number | null
  wellbeing_score: number | null
  self_efficacy_score: number | null
  work_readiness_score: number | null
  stress_status: StressStatus | null
  breakdown_json: Record<string, unknown> | null
  calculation_version: string
}

export interface StaffRecommendation {
  title: string
  reason: string
  action: string
  priority: 'low' | 'medium' | 'high'
  observed_facts: string[]
  hypothesis: string
  questions: string[]
  avoid: string
  next_check_date: string
}

export interface UserRecommendation {
  title: string
  reason: string
  action: string
  amount: string
  alternative: string
}

export interface AnalysisResult {
  summary: string
  strengths: string[]
  concerns: string[]
  trend_analysis: string
  maslow_analysis: string
  adler_analysis: string
  perma_analysis: string
  abc_analysis: string
  choice_theory_analysis: string
  behavioral_economics_analysis: string
  staff_recommendations: StaffRecommendation[]
  user_recommendations: UserRecommendation[]
  questions_for_staff: string[]
  risk_flags: { type: string; detail: string }[]
  confidence: number
  data_limitations: string[]
}

export interface AiAnalysis {
  id: number
  user_id: number
  analysis_date: string
  analysis_type: string
  input_period_start: string | null
  input_period_end: string | null
  model_name: string
  prompt_version: string
  result_json: Partial<AnalysisResult> | null
  status: 'success' | 'fallback' | 'failed'
  error_message: string | null
  created_at: string
}

export type PlanStatus = 'draft' | 'in_review' | 'approved' | 'active' | 'evaluated' | 'closed'

export interface SupportPlan {
  id: number
  user_id: number
  title: string
  status: PlanStatus
  current_issues: string | null
  strengths: string | null
  user_preferences: string | null
  background_hypothesis: string | null
  long_term_goal: string | null
  short_term_goals_json: string[] | null
  support_methods_json: string[] | null
  home_actions_json: string[] | null
  office_actions_json: string[] | null
  user_actions_json: string[] | null
  evaluation_metrics_json: string[] | null
  evaluation_date: string | null
  next_review_date: string | null
  notes: string | null
  created_by: number | null
  approved_by: number | null
  approved_at: string | null
  created_at: string
  updated_at: string
}

export interface PlanVersion {
  id: number
  support_plan_id: number
  version_number: number
  snapshot_json: Record<string, unknown>
  changed_by: number | null
  change_reason: string | null
  created_at: string
}

export interface SupportAction {
  id: number
  user_id: number
  support_plan_id: number | null
  staff_id: number
  action_date: string
  action_content: string
  user_response: string | null
  effect_score: number | null
  next_action: string | null
  created_at: string
}

export interface Goal {
  id: number
  user_id: number
  title: string
  description: string | null
  target_date: string | null
  status: 'active' | 'achieved' | 'paused' | 'closed'
  progress: number
  created_at: string
  updated_at: string
}

export interface RiskAlert {
  id: number
  user_id: number
  user_name: string | null
  alert_type: string
  severity: 'low' | 'medium' | 'high'
  reason: string
  status: 'open' | 'acknowledged'
  acknowledged_by: number | null
  acknowledged_at: string | null
  created_at: string
}

export interface AuditLog {
  id: number
  actor_user_id: number | null
  actor_email: string | null
  action: string
  target_type: string | null
  target_id: number | null
  details_json: Record<string, unknown> | null
  created_at: string
}

export interface ScoreSummary {
  score_date: string
  life_rhythm_score: number | null
  sleep_score: number | null
  mental_score: number | null
  wellbeing_score: number | null
  self_efficacy_score: number | null
  work_readiness_score: number | null
  stress_status: StressStatus | null
}

export interface UserDashboard {
  latest_score: ScoreSummary | null
  score_history: ScoreSummary[]
  sleep_history: { date: string; sleep_hours: number }[]
  stress_history: { date: string; stress_level: number }[]
  today_report: { exists: boolean; is_draft: boolean | null; report_id: number | null }
  report_rate_30d: number
  input_rates_weekly: { label: string; rate: number }[]
  goals: { id: number; title: string; status: string; progress: number }[]
  goal_achievement_rate: number | null
  latest_analysis: {
    id: number
    created_at: string
    status: string
    result: Partial<AnalysisResult> | null
  } | null
  support_plan: { id: number; title: string; status: PlanStatus; next_review_date: string | null } | null
}

export interface StaffDashboard {
  summary: {
    assigned_users: number
    reported_today: number
    open_alerts: number
    urgent_reports_7d: number
  }
  users: {
    user_id: number
    display_name: string
    last_report_date: string | null
    latest_score: ScoreSummary | null
    open_alert_count: number
  }[]
  alerts: {
    id: number
    user_id: number
    user_name: string | null
    alert_type: string
    severity: string
    reason: string
    created_at: string
  }[]
  urgent_reports: {
    id: number
    user_id: number
    user_name: string | null
    report_date: string
    support_content: string | null
  }[]
}

export interface AdminDashboard {
  summary: {
    total_users: number
    total_staff: number
    reported_today: number
    report_rate_today: number
    open_alerts: number
    urgent_reports_7d: number
  }
  input_rate_trend: { date: string; rate: number }[]
  plan_status_counts: Record<string, number>
  alerts: StaffDashboard['alerts']
}
