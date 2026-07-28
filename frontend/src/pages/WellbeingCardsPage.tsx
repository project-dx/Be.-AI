import { useEffect, useMemo, useState } from 'react'
import { errorMessage, wellbeingApi } from '../services/api'
import { useAuth } from '../stores/AuthContext'
import { Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { PrimaryButton } from '../components/form'
import type { WellbeingCard, WellbeingSelection } from '../types'

const CATEGORY_DEFS = [
  { key: 'self', label: 'じぶんのこと', icon: '🌱', chip: 'bg-brand-leaf-soft text-brand-leaf' },
  { key: 'people', label: 'ひととのつながり', icon: '🤝', chip: 'bg-brand-coral-soft text-brand-coral' },
  { key: 'world', label: '社会や世界とのつながり', icon: '🌏', chip: 'bg-brand-sea-soft text-brand-sea' },
] as const

const ORDER_COLORS = ['bg-brand-pink', 'bg-brand-sun', 'bg-brand-sea']

function todayLabel(): string {
  return new Date().toLocaleDateString('ja-JP', { year: 'numeric', month: 'long', day: 'numeric' })
}

export default function WellbeingCardsPage() {
  const { user } = useAuth()
  const [cards, setCards] = useState<WellbeingCard[]>([])
  const [selections, setSelections] = useState<WellbeingSelection[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cardById = useMemo(() => new Map(cards.map((c) => [c.id, c])), [cards])
  const today = new Date().toISOString().slice(0, 10)

  useEffect(() => {
    if (!user) return
    Promise.all([wellbeingApi.cards(), wellbeingApi.selections(user.id)])
      .then(([cardList, history]) => {
        setCards(cardList)
        setSelections(history)
        const todays = history.find((s) => s.selection_date === today)
        if (todays) {
          setSelected(todays.card_ids)
          setNote(todays.note ?? '')
        }
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false))
  }, [user, today])

  const toggle = (id: string) => {
    setSaved(false)
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((c) => c !== id)
      if (prev.length >= 3) return prev // 3枚選択済みなら追加しない
      return [...prev, id]
    })
  }

  const save = async () => {
    if (!user || selected.length !== 3) return
    setSaving(true)
    setError(null)
    try {
      const result = await wellbeingApi.save(user.id, { card_ids: selected, note: note || undefined })
      setSelections((prev) => {
        const rest = prev.filter((s) => s.id !== result.id)
        return [result, ...rest].sort((a, b) => b.selection_date.localeCompare(a.selection_date))
      })
      setSaved(true)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Loading />

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-ink">🌈 ウェルビーイングカード</h1>
        <p className="mt-1.5 text-sm text-ink-soft">
          {todayLabel()}。32枚のカードの中から、いまのあなたが大切にしたいものを
          <span className="font-bold text-ink">3枚</span>選んでください。正解はありません。選んだ順番も大切なヒントになります。
        </p>
      </div>

      <ErrorMessage message={error} />

      {/* 選択状況 */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-2">
            {[0, 1, 2].map((i) => {
              const card = selected[i] ? cardById.get(selected[i]) : null
              return (
                <div
                  key={i}
                  className={`flex min-h-16 w-24 sm:w-32 flex-col items-center justify-center rounded-2xl border-2 px-2 py-2 text-center transition-all ${
                    card ? 'border-transparent bg-paper shadow-card' : 'border-dashed border-line-strong'
                  }`}
                >
                  <span
                    aria-hidden
                    className={`mb-1 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-black text-white ${ORDER_COLORS[i]}`}
                  >
                    {i + 1}
                  </span>
                  {card ? (
                    <span className="text-xs font-bold text-ink leading-tight">{card.label}</span>
                  ) : (
                    <span className="text-xs text-ink-faint">えらぶ</span>
                  )}
                </div>
              )
            })}
          </div>
          <div className="flex-1 min-w-40">
            <input
              value={note}
              onChange={(e) => { setNote(e.target.value); setSaved(false) }}
              placeholder="えらんだ理由や気持ち（かいてもかかなくてもOK）"
              maxLength={1000}
              className="w-full rounded-2xl border border-line-strong bg-white px-3.5 py-2.5 text-sm placeholder:text-ink-faint focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15"
            />
          </div>
          <PrimaryButton onClick={save} disabled={selected.length !== 3 || saving}>
            {saving ? 'ほぞん中…' : saved ? 'ほぞんしました ✓' : `この3枚でほぞん（${selected.length}/3）`}
          </PrimaryButton>
        </div>
      </Card>

      {/* カード一覧 */}
      {CATEGORY_DEFS.map((cat) => (
        <section key={cat.key}>
          <h2 className={`mb-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-bold ${cat.chip}`}>
            <span aria-hidden>{cat.icon}</span>
            {cat.label}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
            {cards
              .filter((c) => c.category === cat.key)
              .map((c) => {
                const order = selected.indexOf(c.id)
                const isSelected = order >= 0
                const isFull = selected.length >= 3 && !isSelected
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => toggle(c.id)}
                    aria-pressed={isSelected}
                    disabled={isFull}
                    className={`relative rounded-2xl border p-3 text-left transition-all ${
                      isSelected
                        ? 'border-transparent bg-white shadow-card-hover ring-4 ring-brand-leaf/25 scale-[1.03]'
                        : isFull
                          ? 'border-line bg-paper opacity-45'
                          : 'border-line bg-white shadow-card hover:shadow-card-hover hover:-translate-y-0.5'
                    }`}
                  >
                    {isSelected && (
                      <span
                        aria-hidden
                        className={`absolute -right-1.5 -top-1.5 flex h-6 w-6 items-center justify-center rounded-full text-xs font-black text-white shadow-pop ${ORDER_COLORS[order]}`}
                      >
                        {order + 1}
                      </span>
                    )}
                    <p className="font-display text-sm font-bold text-ink leading-snug">{c.label}</p>
                    <p className="mt-1 text-[11px] leading-relaxed text-ink-faint">{c.description}</p>
                  </button>
                )
              })}
          </div>
        </section>
      ))}

      {/* これまでの記録 */}
      <Card title="📖 これまでにえらんだカード">
        {selections.length === 0 ? (
          <EmptyState message="まだ記録がありません。はじめの3枚をえらんでみましょう" />
        ) : (
          <ul className="space-y-2.5">
            {selections.map((s) => (
              <li key={s.id} className="flex flex-wrap items-center gap-2 rounded-2xl bg-paper px-4 py-3">
                <span className="text-xs font-bold text-ink-soft w-24">
                  {new Date(`${s.selection_date}T00:00:00`).toLocaleDateString('ja-JP', { month: 'numeric', day: 'numeric', weekday: 'short' })}
                </span>
                {s.card_ids.map((id, i) => (
                  <span key={id} className="inline-flex items-center gap-1.5 rounded-full bg-white border border-line px-2.5 py-1 text-xs font-bold text-ink">
                    <span aria-hidden className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-black text-white ${ORDER_COLORS[i]}`}>
                      {i + 1}
                    </span>
                    {cardById.get(id)?.label ?? id}
                  </span>
                ))}
                {s.note && <span className="w-full text-xs text-ink-soft sm:w-auto sm:ml-1">「{s.note}」</span>}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <p className="text-xs text-ink-faint">
        カードはNTT「わたしたちのウェルビーイングカード」スタンダード版32種（2024年）をもとにしています
      </p>
    </div>
  )
}
