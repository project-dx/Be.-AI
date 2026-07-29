import { useEffect, useState } from 'react'
import { errorMessage, pyramidApi } from '../services/api'
import { useAuth } from '../stores/AuthContext'
import { Card, ErrorMessage, Loading } from '../components/ui'
import { PrimaryButton } from '../components/form'
import { ColorfulPyramidView } from '../components/ColorfulPyramidView'
import type { ColorfulPyramid } from '../types'

/** 利用者本人が自分のカラフルピラミッドを書く画面 */
export default function MyPyramidPage() {
  const { user } = useAuth()
  const [pyramid, setPyramid] = useState<Partial<ColorfulPyramid>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    pyramidApi
      .get(user.id)
      .then(setPyramid)
      .catch((e) => {
        if ((e as { response?: { status?: number } })?.response?.status !== 404) setError(errorMessage(e))
      })
      .finally(() => setLoading(false))
  }, [user])

  const save = async () => {
    if (!user) return
    setSaving(true)
    setError(null)
    try {
      const result = await pyramidApi.save(user.id, pyramid)
      setPyramid(result)
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
        <h1 className="text-xl font-bold text-ink">🔺 わたしのカラフルピラミッド</h1>
        <p className="mt-1.5 text-sm text-ink-soft">
          下から順に、幸せを感じるとき → 好きなこと → なりたい姿 → はたしたい役割 を書いてみましょう。
          あとから何度でも書き直せます。うまく書けなくても大丈夫です。
        </p>
      </div>

      <ErrorMessage message={error} />

      <Card>
        <ColorfulPyramidView
          pyramid={pyramid}
          editable
          onChange={(key, value) => {
            setPyramid((p) => ({ ...p, [key]: value }))
            setSaved(false)
          }}
        />
        <div className="mt-5 flex items-center justify-end gap-3">
          {pyramid.updated_at && (
            <span className="text-xs text-ink-faint">
              最終更新: {new Date(pyramid.updated_at).toLocaleString('ja-JP')}
            </span>
          )}
          <PrimaryButton onClick={save} disabled={saving}>
            {saving ? 'ほぞん中…' : saved ? 'ほぞんしました ✓' : 'ほぞんする'}
          </PrimaryButton>
        </div>
      </Card>
    </div>
  )
}
