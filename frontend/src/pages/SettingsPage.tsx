import { useEffect, useState } from 'react'
import { errorMessage, settingsApi } from '../services/api'
import { Card, ErrorMessage, Loading } from '../components/ui'
import { PrimaryButton, SecondaryButton } from '../components/form'

const groupLabels: Record<string, string> = {
  sleep: '睡眠スコア',
  life_rhythm: '生活リズムスコア',
  mental: 'メンタルスコア',
  wellbeing: '幸福度スコア（PERMA）',
  self_efficacy: '自己効力感スコア',
  work_readiness: '就労準備度スコア',
}

const keyLabels: Record<string, string> = {
  duration: '睡眠時間の適正度',
  quality: '睡眠の質',
  bedtime_stability: '就寝時刻の安定',
  wake_stability: '起床時刻の安定',
  meals: '食事',
  exercise: '運動',
  activity: '日中活動',
  mood: '気分',
  stress: 'ストレス',
  fatigue: '疲労度',
  social: '交流',
  positive_emotion: 'P: 前向きな感情',
  engagement: 'E: 没頭',
  relationships: 'R: 良い人間関係',
  meaning: 'M: 意味・意義',
  accomplishment: 'A: 達成',
  success: '成功体験',
  goals: '目標達成',
  self_eval: '自己評価',
  continuity: '継続日数',
  report_rate: '日報入力',
  work_time: '仕事・勉強時間',
  plan_execution: '予定実行',
  stress_mgmt: 'ストレス管理',
}

export default function SettingsPage() {
  const [weights, setWeights] = useState<Record<string, Record<string, number>> | null>(null)
  const [defaults, setDefaults] = useState<Record<string, Record<string, number>> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    settingsApi
      .getScoringWeights()
      .then((data) => {
        setWeights(data.weights)
        setDefaults(data.defaults)
      })
      .catch((e) => setError(errorMessage(e)))
  }, [])

  const save = async () => {
    if (!weights) return
    setSaving(true)
    setMessage(null)
    setError(null)
    try {
      await settingsApi.updateScoringWeights(weights)
      setMessage('配点を保存しました。次回のスコア計算・再計算から反映されます')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  if (error && !weights) return <ErrorMessage message={error} />
  if (!weights) return <Loading />

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-ink">⚙️ システム設定</h1>
      <p className="text-sm text-ink-soft">
        スコア計算の配点を調整できます。合計が100点になるように設定してください（詳細は docs/scoring-rules.md）
      </p>
      <ErrorMessage message={error} />
      {message && (
        <p role="status" className="rounded-xl border border-emerald-200 bg-brand-leaf-soft px-4 py-3 text-sm text-emerald-800">
          ✅ {message}
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(weights).map(([group, values]) => {
          const total = Object.values(values).reduce((a, b) => a + b, 0)
          return (
            <Card key={group} title={groupLabels[group] ?? group}>
              <div className="space-y-2.5">
                {Object.entries(values).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-3">
                    <label className="text-sm text-ink-soft" htmlFor={`${group}-${key}`}>
                      {keyLabels[key] ?? key}
                    </label>
                    <input
                      id={`${group}-${key}`}
                      type="number"
                      min={0}
                      max={100}
                      value={value}
                      onChange={(e) =>
                        setWeights({
                          ...weights,
                          [group]: { ...values, [key]: Number(e.target.value) },
                        })
                      }
                      className="w-20 rounded-lg border border-line-strong px-2 py-1.5 text-sm text-right"
                    />
                  </div>
                ))}
                <p className={`text-right text-xs font-bold ${total === 100 ? 'text-brand-leaf' : 'text-rose-600'}`}>
                  合計: {total}点{total !== 100 && '（100点になるよう調整してください）'}
                </p>
              </div>
            </Card>
          )
        })}
      </div>

      <div className="flex gap-2">
        <PrimaryButton onClick={save} disabled={saving}>
          {saving ? '保存中…' : '保存する'}
        </PrimaryButton>
        <SecondaryButton onClick={() => defaults && setWeights(structuredClone(defaults))}>
          初期値に戻す
        </SecondaryButton>
      </div>
    </div>
  )
}
