import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { SettingsProvider } from './components/SettingsContext'
import { ToastProvider } from './components/Toast'
import { PublicLayout } from './components/Layout'
import HomePage from './pages/Home'
import BungalowsPage from './pages/Bungalows'
import BungalowDetailPage from './pages/BungalowDetail'
import PaymentPage from './pages/Payment'
import ReservationStatusPage from './pages/ReservationStatus'
import AdminLayout, { AuthProvider } from './pages/admin/AdminLayout'
import LoginPage from './pages/admin/Login'
import DashboardPage from './pages/admin/Dashboard'
import KnowledgePage from './pages/admin/Knowledge'
import BotSettingsPage from './pages/admin/BotSettings'
import RagPage from './pages/admin/Rag'
import VoiceSessionsPage from './pages/admin/VoiceSessions'
import BotTestPage from './pages/admin/BotTest'
import AdminBungalowsPage from './pages/admin/AdminBungalows'
import AdminReservationsPage from './pages/admin/AdminReservations'

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <SettingsProvider>
          <AuthProvider>
            <Routes>
              <Route element={<PublicLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/bungalovlar" element={<BungalowsPage />} />
                <Route path="/bungalovlar/:slug" element={<BungalowDetailPage />} />
                <Route path="/rezervasyon/:code" element={<ReservationStatusPage />} />
                <Route path="*" element={<div className="pt-32 text-center text-stone-600">Sayfa bulunamadı.</div>} />
              </Route>
              <Route path="/odeme/:token" element={<PaymentPage />} />
              <Route path="/admin/giris" element={<LoginPage />} />
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="bilgi-bankasi" element={<KnowledgePage />} />
                <Route path="rag" element={<RagPage />} />
                <Route path="bot-ayarlari" element={<BotSettingsPage />} />
                <Route path="sesli-gorusmeler" element={<VoiceSessionsPage />} />
                <Route path="bot-test" element={<BotTestPage />} />
                <Route path="bungalovlar" element={<AdminBungalowsPage />} />
                <Route path="rezervasyonlar" element={<AdminReservationsPage />} />
              </Route>
            </Routes>
          </AuthProvider>
        </SettingsProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
