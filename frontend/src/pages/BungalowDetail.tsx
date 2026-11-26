import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { BedDouble, Check, Loader2, Maximize2, Users } from 'lucide-react'
import { api } from '../api/client'
import type { Availability, Bungalow } from '../api/types'
import { Calendar } from '../components/Calendar'
import { ErrorBox, Field, SafeImage, Spinner } from '../components/ui'
import { useAsync } from '../lib/useAsync'
import { addDays, errMsg, fmtDate, tl, today } from '../lib/format'

function Gallery({ b }: { b: Bungalow }) {
  const [i, setI] = useState(0)
  const imgs = b.images.length ? b.images : ['']
  return (
    <div>
      <SafeImage src={imgs[i]} alt={b.name} className="w-full h-72 sm:h-[26rem] rounded-3xl" />
      {imgs.length > 1 && (
        <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
          {imgs.map((im, k) => (
            <button key={k} onClick={() => setI(k)} className={`shrink-0 rounded-xl overflow-hidden border-2 ${k === i ? 'border-navy-600' : 'border-transparent opacity-70 hover:opacity-100'}`}>
              <SafeImage src={im} alt={`${b.name} ${k + 1}`} className="w-20 h-14" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function BungalowDetailPage() {
  const { slug = '' } = useParams()
  const { data: b, loading, error } = useAsync(() => api.bungalow(slug), [slug])
  if (loading) return <div className="pt-28"><Spinner /></div>
  if (error || !b) return <div className="max-w-3xl mx-auto px-5 pt-28"><ErrorBox text={error ?? 'Bungalov bulunamadı'} /></div>
  return <Detail b={b} />
}

function Detail({ b }: { b: Bungalow }) {
  const [sp] = useSearchParams()
  const nav = useNavigate()
  const [ci, setCi] = useState(sp.get('check_in') ?? '')
  const [co, setCo] = useState(sp.get('check_out') ?? '')
  const [guests, setGuests] = useState(Math.min(Number(sp.get('guests')) || 2, b.capacity))
  const [avail, setAvail] = useState<Availability | null>(null)
  const [availErr, setAvailErr] = useState<string | null>(null)
  const [checking, setChecking] = useState(false)
  const [form, setForm] = useState({ guest_name: '', guest_email: '', guest_phone: '', note: '' })
  const [busy, setBusy] = useState(false)
  const [submitErr, setSubmitErr] = useState<string | null>(null)

  useEffect(() => {
    setAvail(null); setAvailErr(null)
    if (!ci || !co || co <= ci) return
    let alive = true
    setChecking(true)
    api.availability(b.id, ci, co)
      .then(a => alive && setAvail(a))
      .catch(e => alive && setAvailErr(errMsg(e)))
      .finally(() => alive && setChecking(false))
    return () => { alive = false }
  }, [b.id, ci, co])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitErr(null)
    setBusy(true)
    try {
      const r = await api.createReservation({ bungalow_id: b.id, check_in: ci, check_out: co, guests, ...form, note: form.note || undefined })
      const p = await api.initPayment(r.code)
      nav(p.payment_page_url)
    } catch (err) {
      setSubmitErr(errMsg(err))
      setBusy(false)
    }
  }

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm(f => ({ ...f, [k]: e.target.value }))
  const canBook = !!avail?.available && guests >= 1 && guests <= b.capacity

  return (
    <div className="max-w-6xl mx-auto px-5 pt-24">
      <div className="grid gap-10 lg:grid-cols-[1fr_400px]">
        <div className="min-w-0">
          <Gallery b={b} />
          <h1 className="text-4xl sm:text-5xl text-navy-800 mt-8">{b.name}</h1>
          <div className="flex flex-wrap gap-5 mt-4 text-sm text-navy-700">
            <span className="flex items-center gap-1.5"><Users size={16} />{b.capacity} kişi</span>
            <span className="flex items-center gap-1.5"><BedDouble size={16} />{b.bedrooms} yatak odası</span>
            <span className="flex items-center gap-1.5"><Maximize2 size={16} />{b.size_m2} m²</span>
          </div>
          <p className="mt-6 text-stone-700 leading-relaxed whitespace-pre-line">{b.description}</p>

          {b.amenities.length > 0 && (
            <>
              <h2 className="text-2xl text-navy-800 mt-10 mb-4">Olanaklar</h2>
              <ul className="grid sm:grid-cols-2 gap-2.5">
                {b.amenities.map(a => <li key={a} className="flex items-center gap-2 text-sm text-stone-700"><span className="w-5 h-5 rounded-full bg-navy-100 text-navy-700 flex items-center justify-center"><Check size={12} /></span>{a}</li>)}
              </ul>
            </>
          )}

          <h2 className="text-2xl text-navy-800 mt-10 mb-4">Müsaitlik Takvimi</h2>
          <div className="card p-5">
            <Calendar bungalowId={b.id} checkIn={ci} checkOut={co} onChange={(a, c) => { setCi(a); setCo(c) }} />
          </div>
        </div>

        <aside className="lg:sticky lg:top-24 self-start">
          <form onSubmit={submit} className="card p-6 space-y-4">
            <div className="flex items-baseline gap-1">
              <span className="font-display text-3xl text-navy-800">{tl(b.price_per_night)}</span>
              <span className="text-sm text-stone-500">/ gece</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Giriş"><input type="date" required className="input" min={today()} value={ci} onChange={e => { setCi(e.target.value); if (co && co <= e.target.value) setCo(addDays(e.target.value, 1)) }} /></Field>
              <Field label="Çıkış"><input type="date" required className="input" min={ci ? addDays(ci, 1) : today()} value={co} onChange={e => setCo(e.target.value)} /></Field>
            </div>
            <Field label={`Misafir sayısı (en fazla ${b.capacity})`}>
              <input type="number" min={1} max={b.capacity} className="input" value={guests} onChange={e => setGuests(Number(e.target.value))} />
            </Field>

            <div className="rounded-xl bg-pool-50 border border-pool-100 p-3 text-sm min-h-14">
              {checking ? <span className="flex items-center gap-2 text-stone-500"><Loader2 size={16} className="animate-spin" />Kontrol ediliyor…</span>
                : availErr ? <span className="text-red-700">{availErr}</span>
                : avail ? (avail.available ? (
                  <div className="space-y-1">
                    <div className="flex justify-between text-stone-600"><span>{tl(b.price_per_night)} × {avail.nights} gece</span><span>{tl(avail.total_price)}</span></div>
                    <div className="flex justify-between font-semibold text-navy-800 text-base"><span>Toplam</span><span>{tl(avail.total_price)}</span></div>
                    <div className="text-xs text-stone-500">{fmtDate(ci)} – {fmtDate(co)}</div>
                  </div>
                ) : <span className="text-red-700 font-medium">Seçtiğiniz tarihlerde müsait değil.</span>)
                : <span className="text-stone-500">Fiyat için tarih seçin.</span>}
            </div>

            <hr className="border-pool-100" />
            <Field label="Ad Soyad"><input required className="input" value={form.guest_name} onChange={set('guest_name')} autoComplete="name" /></Field>
            <Field label="E-posta"><input required type="email" className="input" value={form.guest_email} onChange={set('guest_email')} autoComplete="email" /></Field>
            <Field label="Telefon"><input required type="tel" className="input" value={form.guest_phone} onChange={set('guest_phone')} autoComplete="tel" placeholder="05xx xxx xx xx" /></Field>
            <Field label="Not (isteğe bağlı)"><textarea rows={2} className="input" value={form.note} onChange={set('note')} /></Field>
            {submitErr && <ErrorBox text={submitErr} />}
            <button disabled={!canBook || busy} className="btn btn-primary w-full !py-3">
              {busy ? <><Loader2 size={18} className="animate-spin" />İşleniyor…</> : 'Rezervasyon Yap ve Öde'}
            </button>
            <p className="text-xs text-center text-stone-500">Bir sonraki adımda ödeme sayfasına yönlendirileceksiniz.</p>
          </form>
        </aside>
      </div>
    </div>
  )
}
