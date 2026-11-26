import { useEffect, useState, type FormEvent } from 'react'
import { Loader2 } from 'lucide-react'
import { api } from '../../api/client'
import type { Settings } from '../../api/types'
import { ErrorBox, Field, Spinner } from '../../components/ui'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../lib/useAsync'
import { errMsg } from '../../lib/format'
import { PageHead } from './AdminLayout'

export default function BotSettingsPage() {
  const toast = useToast()
  const { data, loading, error } = useAsync(() => api.admin.getSettings(), [])
  const [s, setS] = useState<Settings | null>(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => { if (data) setS(data) }, [data])

  if (loading) return <Spinner />
  if (error || !s) return <ErrorBox text={error ?? 'Ayarlar alınamadı'} />

  const set = (k: keyof Settings) => (e: { target: { value: string } }) => setS({ ...s, [k]: e.target.value })
  const save = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true)
    try { setS(await api.admin.saveSettings(s)); toast.ok('Ayarlar kaydedildi') } catch (e2) { toast.err(errMsg(e2)) } finally { setBusy(false) }
  }

  return (
    <>
      <PageHead title="Bot Ayarları" desc="Tesis bilgilerini ve sohbet asistanının kişiliğini buradan yönetin." />
      <form onSubmit={save} className="space-y-6 max-w-3xl">
        <section className="card p-6 space-y-4">
          <h2 className="text-lg text-navy-800">Tesis Bilgileri</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="Tesis adı"><input className="input" value={s.resort_name} onChange={set('resort_name')} required /></Field>
            <Field label="Slogan"><input className="input" value={s.tagline} onChange={set('tagline')} /></Field>
            <Field label="Telefon"><input className="input" value={s.phone} onChange={set('phone')} /></Field>
            <Field label="E-posta"><input type="email" className="input" value={s.email} onChange={set('email')} /></Field>
            <Field label="Giriş saati"><input className="input" value={s.check_in_time} onChange={set('check_in_time')} placeholder="14:00" /></Field>
            <Field label="Çıkış saati"><input className="input" value={s.check_out_time} onChange={set('check_out_time')} placeholder="11:00" /></Field>
          </div>
          <Field label="Adres"><textarea rows={2} className="input" value={s.address} onChange={set('address')} /></Field>
          <Field label="Harita gömme (embed) URL" hint="Google Maps > Paylaş > Haritayı yerleştir bölümündeki iframe src adresi."><input className="input" value={s.map_embed_url} onChange={set('map_embed_url')} /></Field>
        </section>

        <section className="card p-6 space-y-4">
          <h2 className="text-lg text-navy-800">Sohbet Asistanı</h2>
          <Field label="Bot adı"><input className="input" value={s.bot_name} onChange={set('bot_name')} required /></Field>
          <Field label="Karşılama mesajı" hint="Sohbet penceresi açıldığında ilk gösterilen mesaj."><textarea rows={3} className="input" value={s.bot_welcome_message} onChange={set('bot_welcome_message')} /></Field>
          <Field label="Ek talimatlar" hint="Bota özel yönergeler yazın: konuşma tonu (samimi/resmi), asla söylememesi gerekenler, kampanya vurguları, belirli sorularda yönlendirme vb. Örnek: “Her zaman sen diye hitap et. İndirim sözü verme. Emin olmadığın konuda telefona yönlendir.” Bu metin müşterilere gösterilmez.">
            <textarea rows={12} className="input font-mono !text-[13px]" value={s.bot_extra_instructions} onChange={set('bot_extra_instructions')} />
          </Field>
        </section>

        <section className="card p-6 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg text-navy-800">Sesli Asistan</h2>
            <label className="flex items-center gap-2 text-sm font-semibold text-navy-800 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 accent-[#c9a24b]" checked={s.voice_enabled} onChange={e => setS({ ...s, voice_enabled: e.target.checked })} />
              Sesli asistan açık
            </label>
          </div>
          <Field label="Karşılama cümlesi" hint="Görüşme başlar başlamaz asistanın ilk söyleyeceği söz. Kısa tutun.">
            <textarea rows={2} className="input" value={s.voice_greeting} onChange={set('voice_greeting')} />
          </Field>
          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="Model" hint="gpt-realtime-mini daha ucuzdur, kalitesi daha düşüktür.">
              <select className="input" value={s.voice_model} onChange={set('voice_model')}>
                <option value="gpt-realtime">gpt-realtime</option>
                <option value="gpt-realtime-2.1">gpt-realtime-2.1</option>
                <option value="gpt-realtime-mini">gpt-realtime-mini (ekonomik)</option>
              </select>
            </Field>
            <Field label="Ses">
              <select className="input" value={s.voice_name} onChange={set('voice_name')}>
                {['marin', 'cedar', 'coral', 'sage', 'shimmer', 'verse', 'ballad', 'ash', 'alloy', 'echo'].map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </Field>
            <Field label="Söz kesme hassasiyeti" hint="Düşük: kullanıcı cümle ortasında duraksayınca beklenir (e-posta/telefon söylerken iyi). Yüksek: asistan daha hızlı yanıt verir ama sözü kesebilir.">
              <select className="input" value={s.voice_vad_eagerness} onChange={set('voice_vad_eagerness')}>
                <option value="low">Düşük (sabırlı)</option>
                <option value="medium">Orta (önerilen)</option>
                <option value="high">Yüksek (hızlı)</option>
              </select>
            </Field>
            <Field label="Konuşma hızı" hint="0,25 – 1,5 arası. 1 = normal.">
              <input type="number" step="0.05" min="0.25" max="1.5" className="input" value={s.voice_speed} onChange={e => setS({ ...s, voice_speed: Number(e.target.value) })} />
            </Field>
            <Field label="En uzun görüşme süresi (saniye)" hint="Maliyet kontrolü: bu süre dolunca görüşme otomatik kapanır (30–1800).">
              <input type="number" min="30" max="1800" step="30" className="input" value={s.voice_max_session_seconds} onChange={e => setS({ ...s, voice_max_session_seconds: Number(e.target.value) })} />
            </Field>
          </div>
          <Field label="Telaffuz sözlüğü (JSON)" hint={'Yabancı/marka sözcüklerin sesli okunuşu. Örnek: {"Infinity": "infiniti", "Plunge": "planc"}. Yalnızca konuşmaya uygulanır, ekrandaki yazıyı değiştirmez. Yerleşik sözlüğe ek olarak çalışır.'}>
            <textarea rows={4} className="input font-mono !text-[13px]" value={s.voice_lexicon_json} onChange={set('voice_lexicon_json')} />
          </Field>
        </section>

        <button className="btn btn-primary" disabled={busy}>{busy && <Loader2 size={16} className="animate-spin" />}Kaydet</button>
      </form>
    </>
  )
}
