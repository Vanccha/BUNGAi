import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { Sun, Mail, MapPin, Menu, Phone, X } from 'lucide-react'
import { useSettings } from './SettingsContext'
import { ChatWidget } from './ChatWidget'

export function Header() {
  const { settings } = useSettings()
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const loc = useLocation()
  useEffect(() => { setOpen(false) }, [loc.pathname])
  useEffect(() => {
    const f = () => setScrolled(window.scrollY > 24)
    f(); window.addEventListener('scroll', f)
    return () => window.removeEventListener('scroll', f)
  }, [])
  const solid = scrolled || loc.pathname !== '/' || open
  const links = [
    { to: '/', label: 'Ana Sayfa', end: true },
    { to: '/bungalovlar', label: 'Villalar & Bungalovlar' },
  ]
  return (
    <header className={`fixed top-0 inset-x-0 z-30 transition-all ${solid ? 'bg-foam/95 backdrop-blur shadow-sm text-navy-900' : 'text-white'}`}>
      <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-display text-2xl font-bold">
          <span className={`w-8 h-8 rounded-lg flex items-center justify-center ${solid ? 'bg-gradient-to-br from-gold-400 to-gold-600 text-white' : 'bg-white/20'}`}><Sun size={18} /></span>
          {settings.resort_name}
        </Link>
        <nav className="hidden md:flex items-center gap-7 text-sm font-medium">
          {links.map(l => <NavLink key={l.to} to={l.to} end={l.end} className={({ isActive }) => `hover:opacity-70 ${isActive ? 'underline underline-offset-8 decoration-gold-400' : ''}`}>{l.label}</NavLink>)}
          <a href="/#hizmetler" className="hover:opacity-70">Deneyimler</a>
          <a href="/#iletisim" className="hover:opacity-70">İletişim</a>
          <Link to="/bungalovlar" className="btn btn-primary !py-2">Rezervasyon</Link>
        </nav>
        <button className="md:hidden p-2" onClick={() => setOpen(o => !o)} aria-label="Menü">{open ? <X /> : <Menu />}</button>
      </div>
      {open && (
        <div className="md:hidden bg-foam border-t border-pool-100 px-5 py-4 flex flex-col gap-3 text-navy-800 font-medium">
          {links.map(l => <NavLink key={l.to} to={l.to} end={l.end}>{l.label}</NavLink>)}
          <a href="/#hizmetler">Deneyimler</a>
          <a href="/#iletisim">İletişim</a>
        </div>
      )}
    </header>
  )
}

export function Footer() {
  const { settings: s } = useSettings()
  return (
    <footer id="iletisim" className="bg-navy-900 text-navy-100 mt-24 border-t-4 border-gold-500">
      <div className="max-w-6xl mx-auto px-5 py-14 grid gap-10 md:grid-cols-3">
        <div>
          <div className="font-display text-3xl text-gold-200 mb-3">{s.resort_name}</div>
          <p className="text-sm text-navy-200 max-w-xs">{s.tagline}</p>
        </div>
        <div className="space-y-3 text-sm">
          <h4 className="font-semibold text-gold-300">İletişim</h4>
          {s.phone && <a href={`tel:${s.phone.replace(/\s/g, '')}`} className="flex items-center gap-2 hover:text-white"><Phone size={16} />{s.phone}</a>}
          {s.email && <a href={`mailto:${s.email}`} className="flex items-center gap-2 hover:text-white"><Mail size={16} />{s.email}</a>}
          {s.address && <div className="flex items-start gap-2"><MapPin size={16} className="mt-0.5 shrink-0" />{s.address}</div>}
        </div>
        <div className="text-sm space-y-2">
          <h4 className="font-semibold text-gold-300">Giriş / Çıkış</h4>
          <p>Giriş: {s.check_in_time}</p>
          <p>Çıkış: {s.check_out_time}</p>
        </div>
      </div>
      <div className="border-t border-white/10 py-5 text-center text-xs text-navy-300">
        © {new Date().getFullYear()} {s.resort_name}. Tüm hakları saklıdır. · <Link to="/admin" className="hover:text-white">Yönetim</Link>
      </div>
    </footer>
  )
}

export function PublicLayout() {
  const loc = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [loc.pathname])
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1"><Outlet /></main>
      <Footer />
      <ChatWidget />
    </div>
  )
}
