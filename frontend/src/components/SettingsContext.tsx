import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { PublicSettings } from '../api/types'

export const fallbackSettings: PublicSettings = {
  resort_name: 'BUNGAi', tagline: 'Doğanın kalbinde huzurlu bir tatil', phone: '', email: '', address: '',
  check_in_time: '14:00', check_out_time: '11:00', map_embed_url: '', bot_name: 'Asistan',
  bot_welcome_message: 'Merhaba! Size nasıl yardımcı olabilirim?',
  voice_enabled: false, voice_greeting: '', voice_max_session_seconds: 300,
}
const Ctx = createContext<{ settings: PublicSettings; loaded: boolean }>({ settings: fallbackSettings, loaded: false })
export const useSettings = () => useContext(Ctx)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState(fallbackSettings)
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    api.settings().then(s => setSettings({ ...fallbackSettings, ...s })).catch(() => {}).finally(() => setLoaded(true))
  }, [])
  return <Ctx.Provider value={{ settings, loaded }}>{children}</Ctx.Provider>
}
