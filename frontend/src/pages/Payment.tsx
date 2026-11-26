import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, ChevronDown, Loader2, Lock, ShieldCheck, Wifi, XCircle } from 'lucide-react'
import { api } from '../api/client'
import type { PaymentResult } from '../api/types'
import { ErrorBox, Spinner } from '../components/ui'
import { useAsync } from '../lib/useAsync'
import { errMsg, fmtDate, tl } from '../lib/format'

const TEST_CARDS = [
  { n: '5528 7900 0000 0008', r: 'Başarılı', ok: true },
  { n: '4766 6200 0000 0001', r: 'Başarılı', ok: true },
  { n: '4111 1111 1111 1129', r: 'Başarısız: Yetersiz bakiye', ok: false },
  { n: '4129 1111 1111 1111', r: 'Başarısız: Kart limiti aşıldı / işlem reddedildi', ok: false },
]

const fmtCard = (v: string) => v.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim()
const fmtExp = (v: string) => {
  const d = v.replace(/\D/g, '').slice(0, 4)
  return d.length > 2 ? `${d.slice(0, 2)}/${d.slice(2)}` : d
}
const brand = (n: string) => (n.startsWith('4') ? 'VISA' : /^(5[1-5]|2[2-7])/.test(n) ? 'MASTERCARD' : n.startsWith('9792') ? 'TROY' : 'KART')

type Phase = 'form' | '3ds' | 'processing' | 'done'

export default function PaymentPage() {
  const { token = '' } = useParams()
  const { data, loading, error } = useAsync(() => api.payment(token), [token])
  const [card, setCard] = useState({ number: '', holder: '', exp: '', cvc: '' })
  const [flip, setFlip] = useState(false)
  const [phase, setPhase] = useState<Phase>('form')
  const [result, setResult] = useState<PaymentResult | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [showTest, setShowTest] = useState(false)

  if (loading) return <div className="min-h-screen bg-pool-50"><Spinner label="Ödeme sayfası yükleniyor…" /></div>
  if (error || !data) return <div className="min-h-screen bg-pool-50 p-6"><div className="max-w-md mx-auto mt-20"><ErrorBox text={error ?? 'Ödeme bulunamadı'} /></div></div>

  const r = result?.reservation ?? data.reservation
  const already = data.status === 'success' && !result
  const digits = card.number.replace(/\s/g, '')

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setErr(null)
    const [mm, yy] = card.exp.split('/')
    if (digits.length < 15) return setErr('Kart numarası eksik.')
    if (!mm || !yy || yy.length !== 2 || Number(mm) < 1 || Number(mm) > 12) return setErr('Son kullanma tarihi geçersiz (AA/YY).')
    if (card.cvc.length < 3) return setErr('CVC en az 3 haneli olmalıdır.')
    if (!card.holder.trim()) return setErr('Kart sahibi adını girin.')
    setPhase('3ds')
    await new Promise(res => setTimeout(res, 1400))
    setPhase('processing')
    try {
      const [res] = await Promise.all([
        api.completePayment(token, { card_holder: card.holder.trim(), card_number: digits, expire_month: mm, expire_year: `20${yy}`, cvc: card.cvc }),
        new Promise(res => setTimeout(res, 1200)),
      ])
      setResult(res)
      setPhase('done')
    } catch (e2) {
      setErr(errMsg(e2))
      setPhase('form')
    }
  }

  const demoBadge = (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 text-xs font-bold px-3 py-1 tracking-wide">
      <AlertTriangle size={13} /> DEMO / Test Modu
    </span>
  )

  return (
    <div className="min-h-screen bg-gradient-to-b from-pool-50 to-pool-100 text-slate-800">
      <div className="bg-amber-400 text-amber-950 text-center text-xs font-semibold py-1.5">
        Bu bir demo ödeme sayfasıdır. Gerçek kart bilgisi girmeyin, gerçek tahsilat yapılmaz.
      </div>
      <header className="bg-white border-b border-pool-200">
        <div className="max-w-5xl mx-auto px-5 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-[#1e64ff]"><ShieldCheck size={22} /> iyzico <span className="text-slate-400 font-normal text-sm">demo</span></div>
          <div className="flex items-center gap-3">{demoBadge}<span className="hidden sm:flex items-center gap-1 text-xs text-slate-500"><Lock size={13} />256-bit SSL</span></div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-5 py-8 grid gap-6 md:grid-cols-[340px_1fr]">
        {/* Sipariş özeti */}
        <aside className="bg-white rounded-2xl border border-pool-200 p-6 h-fit">
          <h2 className="font-sans font-semibold text-slate-900 mb-4">Sipariş Özeti</h2>
          <dl className="text-sm space-y-3">
            <div><dt className="text-slate-500 text-xs">Bungalov</dt><dd className="font-medium">{r.bungalow_name}</dd></div>
            <div className="grid grid-cols-2 gap-3">
              <div><dt className="text-slate-500 text-xs">Giriş</dt><dd className="font-medium">{fmtDate(r.check_in)}</dd></div>
              <div><dt className="text-slate-500 text-xs">Çıkış</dt><dd className="font-medium">{fmtDate(r.check_out)}</dd></div>
            </div>
            <div className="flex justify-between"><dt className="text-slate-500">Gece</dt><dd>{r.nights}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Misafir</dt><dd>{r.guests}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Rezervasyon</dt><dd className="font-mono text-xs">{r.code}</dd></div>
            <div className="border-t border-pool-200 pt-3 flex justify-between items-baseline">
              <dt className="font-semibold">Toplam</dt><dd className="text-2xl font-bold text-slate-900">{tl(data.amount)}</dd>
            </div>
          </dl>
        </aside>

        {/* Sağ taraf */}
        <section className="bg-white rounded-2xl border border-pool-200 p-6 sm:p-8">
          {phase === 'done' && result ? (
            <div className="text-center py-8">
              {result.status === 'success'
                ? <CheckCircle2 size={64} className="mx-auto text-emerald-500" />
                : <XCircle size={64} className="mx-auto text-red-500" />}
              <h2 className="font-sans text-2xl font-bold mt-4">{result.status === 'success' ? 'Ödeme Başarılı' : 'Ödeme Başarısız'}</h2>
              <p className="text-slate-600 mt-2">{result.message}</p>
              <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
                <Link to={`/rezervasyon/${r.code}`} className="btn bg-navy-900 text-white hover:bg-navy-700">Rezervasyonu Görüntüle</Link>
                {result.status === 'failure' && (
                  <button className="btn btn-ghost" onClick={() => { setPhase('form'); setResult(null); setErr(null) }}>Tekrar Dene</button>
                )}
              </div>
            </div>
          ) : already ? (
            <div className="text-center py-8">
              <CheckCircle2 size={64} className="mx-auto text-emerald-500" />
              <h2 className="font-sans text-2xl font-bold mt-4">Bu ödeme zaten tamamlandı</h2>
              <Link to={`/rezervasyon/${r.code}`} className="btn bg-navy-900 text-white mt-6">Rezervasyonu Görüntüle</Link>
            </div>
          ) : phase === '3ds' || phase === 'processing' ? (
            <div className="text-center py-16">
              <Loader2 size={48} className="mx-auto animate-spin text-[#1e64ff]" />
              <h2 className="font-sans text-lg font-semibold mt-5">{phase === '3ds' ? '3D Secure doğrulaması yapılıyor…' : 'Ödemeniz işleniyor…'}</h2>
              <p className="text-sm text-slate-500 mt-1">{phase === '3ds' ? 'Bankanızla güvenli bağlantı kuruluyor (demo).' : 'Lütfen sayfayı kapatmayın.'}</p>
            </div>
          ) : (
            <form onSubmit={submit}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="font-sans font-semibold text-slate-900">Kart Bilgileri</h2>
                {demoBadge}
              </div>

              <div className="relative mx-auto w-full max-w-sm aspect-[1.586] rounded-2xl p-5 text-white shadow-xl bg-gradient-to-br from-navy-900 via-navy-700 to-aegean-600 mb-6 overflow-hidden">
                <div className="absolute -right-10 -top-10 w-40 h-40 rounded-full bg-white/10" />
                {!flip ? (
                  <div className="relative h-full flex flex-col justify-between">
                    <div className="flex justify-between items-start"><div className="w-10 h-7 rounded bg-amber-300/80" /><Wifi size={20} className="rotate-90 opacity-70" /></div>
                    <div className="font-mono text-lg sm:text-xl tracking-widest">{(card.number || '•••• •••• •••• ••••').padEnd(19, ' ')}</div>
                    <div className="flex justify-between items-end text-xs">
                      <div><div className="opacity-60 text-[10px]">KART SAHİBİ</div><div className="uppercase tracking-wide truncate max-w-[180px]">{card.holder || 'AD SOYAD'}</div></div>
                      <div><div className="opacity-60 text-[10px]">SKT</div><div>{card.exp || 'AA/YY'}</div></div>
                      <div className="font-bold italic">{brand(digits)}</div>
                    </div>
                  </div>
                ) : (
                  <div className="relative h-full flex flex-col justify-center gap-4">
                    <div className="bg-black/80 h-10 -mx-5" />
                    <div className="bg-white text-slate-900 text-right px-3 py-1.5 rounded font-mono text-sm self-end w-24">{card.cvc || '•••'}</div>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <label className="label !text-slate-600">Kart Numarası</label>
                  <input className="input !border-slate-300 font-mono" inputMode="numeric" autoComplete="cc-number" placeholder="0000 0000 0000 0000" value={card.number} onFocus={() => setFlip(false)} onChange={e => setCard(c => ({ ...c, number: fmtCard(e.target.value) }))} required />
                </div>
                <div>
                  <label className="label !text-slate-600">Kart Üzerindeki İsim</label>
                  <input className="input !border-slate-300 uppercase" autoComplete="cc-name" placeholder="AD SOYAD" value={card.holder} onFocus={() => setFlip(false)} onChange={e => setCard(c => ({ ...c, holder: e.target.value }))} required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label !text-slate-600">Son Kullanma (AA/YY)</label>
                    <input className="input !border-slate-300 font-mono" inputMode="numeric" autoComplete="cc-exp" placeholder="AA/YY" value={card.exp} onFocus={() => setFlip(false)} onChange={e => setCard(c => ({ ...c, exp: fmtExp(e.target.value) }))} required />
                  </div>
                  <div>
                    <label className="label !text-slate-600">CVC</label>
                    <input className="input !border-slate-300 font-mono" inputMode="numeric" autoComplete="cc-csc" placeholder="123" maxLength={4} value={card.cvc} onFocus={() => setFlip(true)} onBlur={() => setFlip(false)} onChange={e => setCard(c => ({ ...c, cvc: e.target.value.replace(/\D/g, '').slice(0, 4) }))} required />
                  </div>
                </div>
              </div>

              {err && <div className="mt-4"><ErrorBox text={err} /></div>}

              <button className="btn w-full mt-6 !py-3.5 bg-navy-900 text-white hover:bg-navy-700 !rounded-xl text-base">
                <Lock size={16} /> {tl(data.amount)} Öde
              </button>
              <p className="text-center text-xs text-slate-500 mt-3">iyzico ile Güvenli Ödeme (demo) · Kart bilgileri saklanmaz</p>

              <div className="mt-6 border border-amber-300 bg-amber-50 rounded-xl">
                <button type="button" onClick={() => setShowTest(s => !s)} className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-amber-900">
                  Test Kartları <ChevronDown size={18} className={`transition ${showTest ? 'rotate-180' : ''}`} />
                </button>
                {showTest && (
                  <div className="px-4 pb-4 text-xs space-y-2">
                    <p className="text-amber-800">Herhangi bir gelecek tarih ve 3 haneli CVC kullanın. Karta tıklayarak formu doldurabilirsiniz.</p>
                    {TEST_CARDS.map(t => (
                      <button type="button" key={t.n} onClick={() => setCard(c => ({ ...c, number: t.n, holder: c.holder || 'TEST KULLANICI', exp: c.exp || '12/30', cvc: c.cvc || '123' }))}
                        className="w-full flex justify-between gap-2 text-left rounded-lg bg-white border border-amber-200 px-3 py-2 hover:border-amber-400">
                        <span className="font-mono">{t.n}</span>
                        <span className={t.ok ? 'text-emerald-700' : 'text-red-700'}>{t.r}</span>
                      </button>
                    ))}
                    <p className="text-amber-800">Diğer geçerli (Luhn) kartlar başarılı, geçersiz numaralar başarısız olur.</p>
                  </div>
                )}
              </div>
            </form>
          )}
        </section>
      </div>
    </div>
  )
}
