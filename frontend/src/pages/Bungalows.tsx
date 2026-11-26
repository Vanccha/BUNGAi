import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { BungalowCard } from '../components/BungalowCard'
import { ErrorBox, Spinner } from '../components/ui'
import { useAsync } from '../lib/useAsync'

export default function BungalowsPage() {
  const [sp] = useSearchParams()
  const { data, loading, error } = useAsync(() => api.bungalows(), [])
  const guests = Number(sp.get('guests') || 0)
  const q = sp.toString() ? `?${sp.toString()}` : ''
  const list = (data ?? []).filter(b => !guests || b.capacity >= guests)
  return (
    <div className="max-w-6xl mx-auto px-5 pt-28">
      <p className="eyebrow">Konaklama</p>
      <h1 className="text-4xl sm:text-5xl text-navy-900 mt-2">Villalar & Bungalovlarımız</h1>
      {sp.get('check_in') && sp.get('check_out') && (
        <p className="mt-3 text-stone-600">{sp.get('check_in')} – {sp.get('check_out')} tarihleri için bir villa veya bungalov seçin; müsaitlik ve fiyat detay sayfasında gösterilir.</p>
      )}
      <div className="mt-10">
        {loading ? <Spinner /> : error ? <ErrorBox text={error} /> : list.length === 0 ? (
          <p className="text-stone-600">Kriterlere uygun villa veya bungalov bulunamadı.</p>
        ) : (
          <div className="grid gap-7 sm:grid-cols-2 lg:grid-cols-3">{list.map(b => <BungalowCard key={b.id} b={b} query={q} />)}</div>
        )}
      </div>
    </div>
  )
}
