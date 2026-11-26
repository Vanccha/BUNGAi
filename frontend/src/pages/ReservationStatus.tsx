import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { CalendarDays, CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react'
import { api } from '../api/client'
import { ErrorBox, Spinner, StatusBadge } from '../components/ui'
import { useAsync } from '../lib/useAsync'
import { errMsg, fmtDate, tl } from '../lib/format'

export default function ReservationStatusPage() {
  const { code = '' } = useParams()
  const nav = useNavigate()
  const { data: r, loading, error } = useAsync(() => api.reservation(code), [code])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  if (loading) return <div className="pt-28"><Spinner /></div>
  if (error || !r) return <div className="max-w-xl mx-auto px-5 pt-28"><ErrorBox text={error ?? 'Rezervasyon bulunamadı'} /></div>

  const retry = async () => {
    setBusy(true); setErr(null)
    try { const p = await api.initPayment(r.code); nav(p.payment_page_url) }
    catch (e) { setErr(errMsg(e)); setBusy(false) }
  }

  const head = {
    confirmed: { icon: <CheckCircle2 size={56} className="text-emerald-500" />, title: 'Rezervasyonunuz Onaylandı', text: 'Ödemeniz alındı. Sizi ağırlamak için sabırsızlanıyoruz!' },
    pending_payment: { icon: <Clock size={56} className="text-amber-500" />, title: 'Ödeme Bekleniyor', text: 'Rezervasyonunuzu tamamlamak için ödemeyi gerçekleştirin. Süre dolarsa tarihler serbest bırakılır.' },
    payment_failed: { icon: <XCircle size={56} className="text-red-500" />, title: 'Ödeme Başarısız', text: 'Ödeme tamamlanamadı. Tekrar deneyebilirsiniz.' },
    cancelled: { icon: <XCircle size={56} className="text-stone-400" />, title: 'Rezervasyon İptal Edildi', text: 'Bu rezervasyon iptal edilmiştir.' },
  }[r.status]

  const rows: [string, string][] = [
    ['Rezervasyon Kodu', r.code], ['Bungalov', r.bungalow_name],
    ['Giriş', fmtDate(r.check_in)], ['Çıkış', fmtDate(r.check_out)],
    ['Gece', String(r.nights)], ['Misafir', String(r.guests)],
    ['Misafir Adı', r.guest_name], ['E-posta', r.guest_email], ['Telefon', r.guest_phone],
  ]
  return (
    <div className="max-w-2xl mx-auto px-5 pt-28">
      <div className="text-center fade-up">
        <div className="flex justify-center">{head.icon}</div>
        <h1 className="text-3xl text-navy-800 mt-4">{head.title}</h1>
        <p className="text-stone-600 mt-2">{head.text}</p>
      </div>
      <div className="card p-6 mt-8">
        <div className="flex items-center justify-between mb-4">
          <span className="flex items-center gap-2 font-semibold text-navy-800"><CalendarDays size={18} />Rezervasyon Detayı</span>
          <StatusBadge status={r.status} />
        </div>
        <dl className="divide-y divide-pool-100 text-sm">
          {rows.map(([k, v]) => <div key={k} className="flex justify-between gap-4 py-2.5"><dt className="text-stone-500">{k}</dt><dd className="font-medium text-right break-all">{v}</dd></div>)}
          {r.note && <div className="flex justify-between gap-4 py-2.5"><dt className="text-stone-500">Not</dt><dd className="text-right">{r.note}</dd></div>}
          <div className="flex justify-between py-3 text-base"><dt className="font-semibold">Toplam</dt><dd className="font-bold text-navy-800">{tl(r.total_price)}</dd></div>
        </dl>
        {err && <div className="mt-3"><ErrorBox text={err} /></div>}
        <div className="flex flex-col sm:flex-row gap-3 mt-5">
          {(r.status === 'payment_failed' || r.status === 'pending_payment') && (
            <button onClick={retry} disabled={busy} className="btn btn-primary flex-1">
              {busy && <Loader2 size={16} className="animate-spin" />}{r.status === 'payment_failed' ? 'Ödemeyi Tekrar Dene' : 'Ödemeye Geç'}
            </button>
          )}
          <Link to="/" className="btn btn-ghost flex-1">Ana Sayfa</Link>
        </div>
      </div>
    </div>
  )
}
