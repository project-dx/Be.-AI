import type { ColorfulPyramid } from '../types'

type PyramidKey = 'mission' | 'vision' | 'passion' | 'wellbeing'

/** 上から順に: ミッション → ビジョン → パッション → ウェルビーイング（土台） */
const LAYERS: {
  key: PyramidKey
  label: string
  question: string
  gradient: string
  widthClass: string
}[] = [
  {
    key: 'mission',
    label: 'ミッション',
    question: 'はたしたい役割は？',
    gradient: 'from-brand-sun to-brand-coral',
    widthClass: 'w-[46%]',
  },
  {
    key: 'vision',
    label: 'ビジョン',
    question: 'どんな自分になりたい？',
    gradient: 'from-brand-leaf to-[#4fae86]',
    widthClass: 'w-[64%]',
  },
  {
    key: 'passion',
    label: 'パッション',
    question: '好きなこと・夢中になれることは？',
    gradient: 'from-brand-plum to-brand-pink',
    widthClass: 'w-[82%]',
  },
  {
    key: 'wellbeing',
    label: 'ウェルビーイング（幸せ）',
    question: 'どんなときに幸せを感じる？',
    gradient: 'from-brand-sea to-[#3f7fc4]',
    widthClass: 'w-full',
  },
]

export function ColorfulPyramidView({
  pyramid,
  editable = false,
  onChange,
}: {
  pyramid: Partial<ColorfulPyramid>
  editable?: boolean
  onChange?: (key: PyramidKey, value: string) => void
}) {
  return (
    <div className="flex flex-col items-center gap-2">
      {LAYERS.map((layer) => {
        const value = (pyramid[layer.key] as string | null) ?? ''
        return (
          <div key={layer.key} className={`${layer.widthClass} max-w-xl`}>
            <div
              className={`rounded-2xl bg-gradient-to-br ${layer.gradient} px-4 py-3 text-white shadow-card`}
            >
              <p className="font-display text-sm font-black tracking-wide">{layer.label}</p>
              <p className="text-[11px] text-white/85">{layer.question}</p>
            </div>
            {editable ? (
              <textarea
                rows={2}
                aria-label={layer.label}
                placeholder={layer.question}
                value={value}
                onChange={(e) => onChange?.(layer.key, e.target.value)}
                className="mt-1.5 w-full rounded-2xl border border-line-strong bg-white px-3 py-2 text-sm placeholder:text-ink-faint focus:border-brand-sea focus:outline-none focus:ring-4 focus:ring-brand-sea/15"
              />
            ) : (
              value && <p className="mt-1.5 px-1 text-sm leading-relaxed text-ink">{value}</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
