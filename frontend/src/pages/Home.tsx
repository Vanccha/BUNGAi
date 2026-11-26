import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Baby, Calendar, ChevronDown, Flower2, MapPin, Quote, Star, Sunset, Umbrella, Waves, Wine } from 'lucide-react'
import { api } from '../api/client'
import { useSettings } from '../components/SettingsContext'
import { BungalowCard } from '../components/BungalowCard'
import { ErrorBox, SafeImage, Spinner } from '../components/ui'
import { Reveal } from '../lib/useReveal'
import { useAsync } from '../lib/useAsync'
import { addDays, today } from '../lib/format'
import { EXPERIENCE_IMG, GALLERY, HERO, LOCATION_IMG, THUMB } from '../content/images'

const experiences = [
  { icon: Waves, title: 'Sonsuzluk Havuzu', text: 'Denizle birleşen ortak infinity havuzda gün boyu serinleyin.', img: EXPERIENCE_IMG.pool },
  { icon: Umbrella, title: 'Beach Club', text: 'Özel plajda şezlong, şemsiye ve havlu servisi bizden.', img: EXPERIENCE_IMG.beach },
  { icon: Flower2, title: 'Spa & Masaj', text: 'Güneşin yorgunluğunu hamam ve aromaterapi ile atın.', img: EXPERIENCE_IMG.spa },
  { icon: Sunset, title: 'Gün Batımı Akşam Yemeği', text: 'Deniz manzaralı terasta taze Ege mezeleri ve balık.', img: EXPERIENCE_IMG.dinner },
  { icon: Baby, title: 'Çocuk Kulübü', text: 'Çocuklar için güvenli havuz, animasyon ve oyun alanı.', img: EXPERIENCE_IMG.kids },
  { icon: Wine, title: 'Havuz Başı Kokteyl', text: 'Havuzunuzun kenarında serinleten kokteyller ve meyve tabakları.', img: THUMB.womanFloating },
]
const reviews = [
  { name: 'Elif K.', text: 'Özel havuzumuzda sabah kahvemizi içip denize karşı güne başladık. Tam bir rüya tatil!', stars: 5 },
  { name: 'Mehmet & Ayşe', text: 'Çocuklarla geldik; çocuk kulübü ve havuz sayesinde hepimiz çok eğlendik. Villa tertemizdi.', stars: 5 },
  { name: 'Can T.', text: 'Gün batımı yemeği ve beach club harikaydı. Sohbet asistanı rezervasyonu çok kolaylaştırdı.', stars: 5 },
]

function SectionHead({ eyebrow, title, desc }: { eyebrow: string; title: string; desc?: string }) {
  return (
    <Reveal className="text-center mb-12">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="text-4xl sm:text-5xl text-navy-900 mt-2">{title}</h2>
      <div className="gold-divider" />
      {desc && <p className="text-navy-700/80 mt-4 max-w-xl mx-auto">{desc}</p>}
    </Reveal>
  )
}

export default function HomePage() {
  const { settings: s } = useSettings()
  const nav = useNavigate()
  const { data, loading, error } = useAsync(() => api.bungalows(), [])
  const [ci, setCi] = useState(addDays(today(), 7))
  const [co, setCo] = useState(addDays(today(), 10))
  const [guests, setGuests] = useState(2)

  const search = (e: FormEvent) => {
    e.preventDefault()
    nav(`/bungalovlar?check_in=${ci}&check_out=${co}&guests=${guests}`)
  }

  return (
    <>
      <section className="relative min-h-[92vh] flex items-center justify-center text-center text-white overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-navy-800 via-aegean-600 to-pool-300" />
        <img src={HERO} alt="" onError={e => (e.currentTarget.style.display = 'none')} className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-navy-900/60 via-navy-900/10 to-navy-900/70" />
        <div className="relative px-5 pt-24 pb-28 max-w-3xl fade-up">
          <p className="uppercase tracking-[0.35em] text-xs text-gold-200 mb-5">Özel Havuzlu Villa & Bungalov</p>
          <h1 className="text-5xl sm:text-7xl leading-[1.05] drop-shadow-lg">{s.resort_name}</h1>
          <div className="gold-divider" />
          <p className="mt-5 text-lg sm:text-xl text-white/90 max-w-xl mx-auto">{s.tagline}</p>
          <form onSubmit={search} className="mt-10 bg-white/95 backdrop-blur text-navy-900 rounded-3xl p-4 sm:p-5 shadow-2xl ring-1 ring-gold-300 grid gap-3 sm:grid-cols-[1fr_1fr_100px_auto] text-left items-end">
            <div><label className="label">Giriş</label><input type="date" className="input" min={today()} value={ci} onChange={e => { setCi(e.target.value); if (e.target.value >= co) setCo(addDays(e.target.value, 1)) }} required /></div>
            <div><label className="label">Çıkış</label><input type="date" className="input" min={addDays(ci, 1)} value={co} onChange={e => setCo(e.target.value)} required /></div>
            <div><label className="label">Kişi</label><input type="number" min={1} max={12} className="input" value={guests} onChange={e => setGuests(Math.max(1, Number(e.target.value)))} /></div>
            <button className="btn btn-primary !py-3"><Calendar size={16} />Müsaitlik Ara</button>
          </form>
        </div>
        <a href="#villalar" aria-label="Aşağı kaydır" className="absolute bottom-6 left-1/2 -translate-x-1/2 text-white/80 animate-bounce"><ChevronDown /></a>
      </section>

      <section id="villalar" className="max-w-6xl mx-auto px-5 pt-24 scroll-mt-16">
        <SectionHead eyebrow="Konaklama" title="Özel Havuzlu Villalar" desc="Denize yürüme mesafesinde, her biri kendi havuzuna sahip villa ve bungalovlarımız." />
        {loading ? <Spinner label="Villalar yükleniyor…" /> : error ? <ErrorBox text={error} /> : (
          <div className="grid gap-7 sm:grid-cols-2 lg:grid-cols-3">
            {data?.slice(0, 6).map((b, i) => <Reveal key={b.id} delay={i * 80}><BungalowCard b={b} query={`?check_in=${ci}&check_out=${co}&guests=${guests}`} /></Reveal>)}
          </div>
        )}
        <div className="text-center mt-10"><Link to="/bungalovlar" className="btn btn-ghost">Tüm Villaları Gör</Link></div>
      </section>

      <section id="hizmetler" className="max-w-6xl mx-auto px-5 pt-28 scroll-mt-16">
        <SectionHead eyebrow="Deneyimler" title="Tatilin Her Anı Güneşli" />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {experiences.map((x, i) => (
            <Reveal key={x.title} delay={(i % 3) * 90}>
              <div className="card overflow-hidden group h-full">
                <div className="relative h-44 overflow-hidden">
                  <SafeImage src={x.img} alt={x.title} className="w-full h-full group-hover:scale-110 transition duration-[1200ms]" />
                  <div className="absolute inset-0 bg-gradient-to-t from-navy-900/50 to-transparent" />
                  <div className="absolute bottom-0 left-5 translate-y-1/2 w-12 h-12 rounded-2xl bg-gradient-to-br from-gold-300 to-gold-600 text-white flex items-center justify-center shadow-lg"><x.icon size={22} /></div>
                </div>
                <div className="px-5 pb-6 pt-9">
                  <h3 className="text-2xl font-semibold text-navy-900">{x.title}</h3>
                  <p className="text-sm text-navy-700/75 mt-1.5">{x.text}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-5 pt-28">
        <SectionHead eyebrow="Galeri" title="Havuz Başında Yaz Keyfi" />
        <div className="grid grid-cols-2 md:grid-cols-4 auto-rows-[160px] sm:auto-rows-[200px] gap-3">
          {GALLERY.map((g, i) => (
            <Reveal key={g.src} delay={(i % 4) * 70} className={`${g.span ?? ''} overflow-hidden rounded-2xl group`}>
              <SafeImage src={g.src} alt={g.alt} className="w-full h-full group-hover:scale-110 transition duration-[1200ms]" />
            </Reveal>
          ))}
        </div>
      </section>

      <section className="mt-28 relative text-white py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-navy-900 via-navy-700 to-aegean-600" />
        <div className="relative max-w-6xl mx-auto px-5">
          <Reveal className="text-center mb-12">
            <p className="eyebrow !text-gold-300">Misafirlerimiz</p>
            <h2 className="text-4xl sm:text-5xl mt-2">Ne Diyorlar?</h2>
            <div className="gold-divider" />
          </Reveal>
          <div className="grid gap-6 md:grid-cols-3">
            {reviews.map((r, i) => (
              <Reveal key={r.name} delay={i * 100}>
                <figure className="rounded-3xl bg-white/10 backdrop-blur ring-1 ring-white/20 p-6 h-full">
                  <Quote className="text-gold-300 mb-3" />
                  <blockquote className="text-white/90 text-sm leading-relaxed">{r.text}</blockquote>
                  <figcaption className="mt-4 flex items-center justify-between text-sm">
                    <span className="font-semibold text-gold-200">{r.name}</span>
                    <span className="flex text-gold-300">{Array.from({ length: r.stars }).map((_, k) => <Star key={k} size={16} fill="currentColor" />)}</span>
                  </figcaption>
                </figure>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-5 pt-24">
        <SectionHead eyebrow="Konum" title="Bizi Bulun" desc={s.address} />
        <Reveal>
          {s.map_embed_url ? (
            <iframe title="Harita" src={s.map_embed_url} className="w-full h-96 rounded-3xl border-0 shadow-lg" loading="lazy" referrerPolicy="no-referrer-when-downgrade" />
          ) : (
            <div className="relative h-64 rounded-3xl overflow-hidden">
              <SafeImage src={LOCATION_IMG} alt="Denize yakın villalar" className="w-full h-full" />
              <div className="absolute inset-0 bg-navy-900/45 flex items-center justify-center text-white gap-2"><MapPin size={20} />Harita yakında eklenecek</div>
            </div>
          )}
        </Reveal>
      </section>
    </>
  )
}
