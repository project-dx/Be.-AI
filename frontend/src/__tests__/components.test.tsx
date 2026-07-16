import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState, ScoreCard, Badge, AiDisclaimer } from '../components/ui'
import { TrendLineChart } from '../components/charts'

describe('ScoreCard', () => {
  it('スコアと単位を表示する', () => {
    render(<ScoreCard title="睡眠スコア" icon="😴" value={78} />)
    expect(screen.getByText('睡眠スコア')).toBeInTheDocument()
    expect(screen.getByText('78')).toBeInTheDocument()
    expect(screen.getByText('点')).toBeInTheDocument()
  })

  it('値がnullの場合は「データなし」を表示する', () => {
    render(<ScoreCard title="睡眠スコア" icon="😴" value={null} />)
    expect(screen.getByText('データなし')).toBeInTheDocument()
  })
})

describe('EmptyState', () => {
  it('空状態メッセージを日本語で表示する', () => {
    render(<EmptyState message="まだデータがありません" />)
    expect(screen.getByText('まだデータがありません')).toBeInTheDocument()
  })
})

describe('TrendLineChart', () => {
  it('データが空の場合は壊れずに空状態を表示する', () => {
    render(<TrendLineChart data={[]} series={[{ key: 'v', name: '値', color: '#000' }]} />)
    expect(screen.getByText(/表示できるデータがまだありません/)).toBeInTheDocument()
  })
})

describe('Badge', () => {
  it('ラベルをテキストで表示する（色だけに依存しない）', () => {
    render(<Badge label="至急" className="bg-rose-600 text-white" />)
    expect(screen.getByText('至急')).toBeInTheDocument()
  })
})

describe('AiDisclaimer', () => {
  it('医療診断ではない旨の注意書きを表示する', () => {
    render(<AiDisclaimer />)
    expect(screen.getByText(/医療診断ではなく/)).toBeInTheDocument()
  })
})
