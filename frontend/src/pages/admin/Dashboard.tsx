import { CalendarCheck, Clock, TrendingUp, Wallet } from 'lucide-react'
import { api } from '../../api/client'
import { ErrorBox, Spinner, StatusBadge } from '../../components/ui'
import { useAsync } from '../../lib/useAsync'
import { fmtDate, tl } from '../../lib/format'
import { PageHead } from './AdminLayout'

export default function DashboardPage() {
  const { data, loading, error } = useAsync(() => api.admin.stats(), [])
  if (loading) return <Spinner />
  if (error || !data) return <ErrorBox text={error ?? 'Veri alınamadı'} />
  const cards = [
    { label: 'Toplam Rezervasyon', value: String(data.total_reservations), icon: CalendarCheck, color: 'bg-navy-100 text-navy-700' },
    { label: 'Onaylanan', value: String(data.confirmed), icon: TrendingUp, color: 'bg-emerald-100 text-emerald-700' },
    { label: 'Ödeme Bekleyen', value: String(data.pending), icon: Clock, color: 'bg-amber-100 text-amber-700' },
    { label: 'Onaylı Gelir', value: tl(data.revenue_confirmed), icon: Wallet, color: 'bg-pool-200 text-gold-600' },
  ]
  return (
    <>
      <PageHead title="Panel" desc="Rezervasyonlarınıza genel bakış." />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(c => (
          <div key={c.label} className="card p-5 flex items-center gap-4">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${c.color}`}><c.icon size={22} /></div>
            <div><div className="text-xs text-stone-500">{c.label}</div><div className="text-2xl font-display text-navy-800">{c.value}</div></div>
          </div>
        ))}
      </div>
      <h2 className="text-xl text-navy-800 mt-10 mb-3">Yaklaşan Girişler</h2>
      <div className="card overflow-x-auto">
        {data.upcoming_checkins.length === 0 ? <p className="p-6 text-sm text-stone-500">Yaklaşan giriş yok.</p> : (
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-stone-500 border-b border-pool-100"><tr><th className="p-3">Kod</th><th className="p-3">Misafir</th><th className="p-3">Bungalov</th><th className="p-3">Giriş</th><th className="p-3">Çıkış</th><th className="p-3">Durum</th></tr></thead>
            <tbody>
              {data.upcoming_checkins.map(r => (
                <tr key={r.id} className="border-b border-pool-50 last:border-0">
                  <td className="p-3 font-mono text-xs">{r.code}</td><td className="p-3">{r.guest_name}</td><td className="p-3">{r.bungalow_name}</td>
                  <td className="p-3 whitespace-nowrap">{fmtDate(r.check_in)}</td><td className="p-3 whitespace-nowrap">{fmtDate(r.check_out)}</td><td className="p-3"><StatusBadge status={r.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
