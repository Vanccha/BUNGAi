import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { Link, Navigate, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, CalendarCheck, Database, FlaskConical, Home, LayoutDashboard, LogOut, Menu, Mic, Settings, X } from 'lucide-react'
import { getToken, setToken, setUnauthorizedHandler } from '../../api/client'
import { useToast } from '../../components/Toast'

const AuthCtx = createContext<{ token: string | null; login: (t: string) => void; logout: () => void }>({ token: null, login() {}, logout() {} })
export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTok] = useState<string | null>(getToken())
  const login = useCallback((t: string) => { setToken(t); setTok(t) }, [])
  const logout = useCallback(() => { setToken(null); setTok(null) }, [])
  useEffect(() => {
    setUnauthorizedHandler(() => logout())
    return () => setUnauthorizedHandler(null)
  }, [logout])
  return <AuthCtx.Provider value={{ token, login, logout }}>{children}</AuthCtx.Provider>
}

const nav = [
  { to: '/admin', label: 'Panel', icon: LayoutDashboard, end: true },
  { to: '/admin/bilgi-bankasi', label: 'Chatbot Bilgi Bankası', icon: BookOpen },
  { to: '/admin/rag', label: 'RAG & Arama', icon: Database },
  { to: '/admin/bot-ayarlari', label: 'Bot Ayarları', icon: Settings },
  { to: '/admin/sesli-gorusmeler', label: 'Sesli Görüşmeler', icon: Mic },
  { to: '/admin/bot-test', label: 'Bot Test', icon: FlaskConical },
  { to: '/admin/bungalovlar', label: 'Villalar & Bungalovlar', icon: Home },
  { to: '/admin/rezervasyonlar', label: 'Rezervasyonlar', icon: CalendarCheck },
]

export default function AdminLayout() {
  const { token, logout } = useAuth()
  const loc = useLocation()
  const go = useNavigate()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  useEffect(() => { setOpen(false) }, [loc.pathname])

  if (!token) return <Navigate to="/admin/giris" replace state={{ from: loc.pathname }} />

  const side = (
    <div className="flex flex-col h-full">
      <Link to="/admin" className="font-display text-3xl text-gold-200 px-6 py-6">BUNGAi <span className="text-xs font-sans text-navy-300 block">Yönetim Paneli</span></Link>
      <nav className="flex-1 px-3 space-y-1">
        {nav.map(n => (
          <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-gradient-to-r from-gold-300 to-gold-500 text-navy-900 font-semibold' : 'text-navy-100 hover:bg-white/10'}`}>
            <n.icon size={18} />{n.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 space-y-1">
        <Link to="/" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-navy-200 hover:bg-white/10">Siteyi Görüntüle</Link>
        <button onClick={() => { logout(); toast.ok('Çıkış yapıldı'); go('/admin/giris') }} className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-navy-200 hover:bg-white/10"><LogOut size={18} />Çıkış Yap</button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-navy-50/60 lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="hidden lg:block bg-navy-900 sticky top-0 h-screen">{side}</aside>
      <div className="lg:hidden flex items-center justify-between bg-navy-900 text-pool-100 px-4 h-14 sticky top-0 z-30">
        <span className="font-display text-lg">BUNGAi Yönetim</span>
        <button onClick={() => setOpen(true)} aria-label="Menü"><Menu /></button>
      </div>
      {open && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="w-72 bg-navy-900 relative">{side}<button className="absolute top-4 right-4 text-white" onClick={() => setOpen(false)}><X /></button></div>
          <div className="flex-1 bg-black/40" onClick={() => setOpen(false)} />
        </div>
      )}
      <main className="p-5 sm:p-8 min-w-0"><Outlet /></main>
    </div>
  )
}

export function PageHead({ title, desc, children }: { title: string; desc?: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 mb-6">
      <div>
        <h1 className="text-3xl text-navy-900">{title}</h1>
        {desc && <p className="text-sm text-stone-600 mt-1 max-w-2xl">{desc}</p>}
      </div>
      {children}
    </div>
  )
}
