import { useState } from 'react'
import { api } from '../../api/client'
import type { ReservationStatus } from '../../api/types'
import { ErrorBox, Spinner, StatusBadge } from '../../components/ui'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../lib/useAsync'
import { errMsg, fmtDate, statusLabel, tl } from '../../lib/format'
import { PageHead } from './AdminLayout'

const STATUSES = Object.keys(statusLabel) as ReservationStatus[]

export default function AdminReservationsPage() {
  const toast = useToast()
  const [filter, setFilter] = useState('')
  const { data, loading, error, reload } = useAsync(() => api.admin.reservations(filter || undefined), [filter])

  const change = async (id: number, status: ReservationStatus) => {
    try { await api.admin.setReservationStatus(id, status); toast.ok('Durum güncellendi'); await reload() } catch (e) { toast.err(errMsg(e)) }
  }

  return (
    <>
      <PageHead title="Rezervasyonlar">
        <select className="input !w-auto" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">Tüm durumlar</option>
          {STATUSES.map(s => <option key={s} value={s}>{statusLabel[s]}</option>)}
        </select>
      </PageHead>
      {loading ? <Spinner /> : error ? <ErrorBox text={error} /> : (
        <div className="card overflow-x-auto">
          {data?.length === 0 ? <p className="p-6 text-sm text-stone-500">Rezervasyon yok.</p> : (
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-stone-500 border-b border-pool-100">
                <tr><th className="p-3">Kod</th><th className="p-3">Misafir</th><th className="p-3">Bungalov</th><th className="p-3">Tarih</th><th className="p-3">Tutar</th><th className="p-3">Kaynak</th><th className="p-3">Durum</th><th className="p-3">Değiştir</th></tr>
              </thead>
              <tbody>
                {data?.map(r => (
                  <tr key={r.id} className="border-b border-pool-50 last:border-0 align-top">
                    <td className="p-3 font-mono text-xs">{r.code}</td>
                    <td className="p-3"><div className="font-medium">{r.guest_name}</div><div className="text-xs text-stone-500">{r.guest_phone}</div></td>
                    <td className="p-3">{r.bungalow_name}</td>
                    <td className="p-3 whitespace-nowrap">{fmtDate(r.check_in)}<br /><span className="text-xs text-stone-500">{r.nights} gece · {r.guests} kişi</span></td>
                    <td className="p-3 whitespace-nowrap">{tl(r.total_price)}</td>
                    <td className="p-3">{r.source === 'chatbot' ? 'Chatbot' : r.source === 'voice' ? 'Sesli' : 'Web'}</td>
                    <td className="p-3"><StatusBadge status={r.status} /></td>
                    <td className="p-3">
                      <select className="input !py-1 !text-xs !w-auto" value={r.status} onChange={e => change(r.id, e.target.value as ReservationStatus)}>
                        {STATUSES.map(s => <option key={s} value={s}>{statusLabel[s]}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </>
  )
}
