import { useEffect, useMemo, useState } from 'react'
import { errorMessage, wellbeingApi } from '../../services/api'
import { Card, EmptyState, ErrorMessage, Loading } from '../../components/ui'
import { formatDate } from '../../utils/labels'
import type { WellbeingCard, WellbeingSelection } from '../../types'

const ORDER_COLORS = ['bg-brand-pink', 'bg-brand-sun', 'bg-brand-sea']

/** 利用者が選んだウェルビーイングカードの履歴（スタッフ・管理者向けの閲覧） */
export default function WellbeingSelectionsPanel({ userId }: { userId: number }) {
  const [cards, setCards] = useState<WellbeingCard[]>([])
  const [selections, setSelections] = useState<WellbeingSelection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([wellbeingApi.cards(), wellbeingApi.selections(userId)])
      .then(([cardList, history]) => {
        setCards(cardList)
        setSelections(history)
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false))
  }, [userId])

  const cardById = useMemo(() => new Map(cards.map((c) => [c.id, c])), [cards])

  /** よく選ばれているカードの集計（選ばれた回数の多い順） */
  const frequency = useMemo(() => {
    const counts = new Map<string, number>()
    for (const s of selections) {
      for (const id of s.card_ids) counts.set(id, (counts.get(id) ?? 0) + 1)
    }
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
  }, [selections])

  if (loading) return <Card><Loading /></Card>

  return (
    <div className="space-y-4">
      <ErrorMessage message={error} />

      {selections.length === 0 ? (
        <Card title="🌈 ウェルビーイングカード">
          <EmptyState message="本人がまだカードを選んでいません。利用者のメニュー「カードをえらぶ」から記録できます" />
        </Card>
      ) : (
        <>
          <Card title="⭐ よく選ばれているカード" accent="text-brand-plum">
            <p className="mb-3 text-xs text-ink-soft">
              くり返し選ばれているカードは、本人が大切にしている価値観のヒントになります
            </p>
            <div className="flex flex-wrap gap-2">
              {frequency.map(([id, count]) => (
                <span key={id} className="rounded-full bg-brand-plum-soft px-3 py-1.5 text-sm font-bold text-ink">
                  {cardById.get(id)?.label ?? id}
                  <span className="ml-1.5 text-xs text-brand-plum">{count}回</span>
                </span>
              ))}
            </div>
          </Card>

          <Card title="📖 選んだ記録">
            <ul className="space-y-2.5">
              {selections.map((s) => (
                <li key={s.id} className="rounded-2xl bg-paper px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="w-20 text-xs font-bold text-ink-soft">{formatDate(s.selection_date)}</span>
                    {s.card_ids.map((id, i) => {
                      const card = cardById.get(id)
                      return (
                        <span
                          key={id}
                          title={card?.description}
                          className="inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-2.5 py-1 text-xs font-bold text-ink"
                        >
                          <span aria-hidden className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-black text-white ${ORDER_COLORS[i]}`}>
                            {i + 1}
                          </span>
                          {card?.label ?? id}
                        </span>
                      )
                    })}
                  </div>
                  {s.note && <p className="mt-1.5 text-xs text-ink-soft">「{s.note}」</p>}
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </div>
  )
}
