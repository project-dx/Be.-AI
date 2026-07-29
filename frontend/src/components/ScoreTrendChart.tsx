import { chartColors, SimpleBarChart } from './charts'

type ScoreEntry = { label: string; before: number | null; after: number | null; diff?: number }

/**
 * モニタリング評価の「日々の状態の推移」をグラフで表示する。
 *
 * 表示している数値は日報から自動計算された6つのスコア（0〜100点）で、
 * 選んだ期間を前半・後半に分けてそれぞれの平均を比べたもの。
 */
export function ScoreTrendChart({ scores }: { scores: Record<string, ScoreEntry> }) {
  const entries = Object.values(scores).filter((s) => s.before != null || s.after != null)
  if (entries.length === 0) return null

  // データがない期間は 0 ではなく null にする（0点と「記録なし」を区別するため）
  const data = entries.map((s) => ({
    label: s.label,
    before: s.before,
    after: s.after,
  }))
  const missingHalf = entries.some((s) => s.before == null || s.after == null)

  // 変化が大きい項目だけを言葉でも補足する（グラフだけだと読み取りに時間がかかるため）
  const changed = entries
    .filter((s) => s.diff != null && Math.abs(s.diff) >= 5)
    .sort((a, b) => Math.abs(b.diff ?? 0) - Math.abs(a.diff ?? 0))

  return (
    <div>
      <p className="text-sm font-bold text-ink">📊 日々の状態の推移</p>
      <p className="mb-2 text-xs text-ink-soft">
        日報から自動計算したスコア（0〜100点）を、期間の前半と後半に分けて平均で比べています
      </p>

      <SimpleBarChart
        data={data}
        series={[
          { key: 'before', name: '期間の前半', color: chartColors.blue },
          { key: 'after', name: '期間の後半', color: chartColors.green },
        ]}
        yDomain={[0, 100]}
        unit="点"
        height={260}
      />

      {missingHalf && (
        <p className="mt-1 text-xs text-ink-faint">
          ※ 棒が表示されていない項目は、その期間に日報の記録がなくスコアを算出できていません
        </p>
      )}

      {changed.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {changed.map((s) => {
            const diff = s.diff as number
            const up = diff > 0
            return (
              <span
                key={s.label}
                className={`rounded-full px-3 py-1 text-xs font-bold ${
                  up ? 'bg-brand-leaf-soft text-brand-leaf' : 'bg-brand-coral-soft text-brand-coral'
                }`}
              >
                {s.label} {s.before} → {s.after}点（{up ? '+' : ''}{diff}）
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}
