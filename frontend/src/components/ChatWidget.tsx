import { useState } from 'react'
import { MessageCircle, Mic, X } from 'lucide-react'
import { api } from '../api/client'
import { ChatPanel } from './ChatPanel'
import { VoicePanel } from './VoicePanel'
import { useSettings } from './SettingsContext'
import { voiceSupported } from '../lib/useVoiceAssistant'

export function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [voice, setVoice] = useState(false) // sesli mod açık mı
  const { settings } = useSettings()
  const voiceOn = settings.voice_enabled && voiceSupported()
  const toggle = () => { setMounted(true); setOpen(o => !o) }
  const openVoice = () => { setMounted(true); setOpen(true); setVoice(true) }
  const frame = 'fixed z-50 inset-0 sm:inset-auto sm:bottom-24 sm:right-6 sm:w-[390px] sm:h-[600px] sm:max-h-[calc(100vh-8rem)] sm:rounded-3xl overflow-hidden shadow-2xl border border-gold-300'
  return (
    <>
      {mounted && (
        <div className={`${frame} ${open ? 'pop' : 'hidden'}`}>
          {/* Yazılı sohbet açık kalır (durumu korunsun), sesli mod üstüne biner */}
          <ChatPanel
            className={`h-full ${voice ? 'hidden' : ''}`}
            send={api.chat}
            botName={settings.bot_name}
            welcome={settings.bot_welcome_message}
            storageKey="bungai_chat_session"
            onClose={() => setOpen(false)}
            onVoice={voiceOn ? () => setVoice(true) : undefined}
          />
          {voice && voiceOn && (
            <VoicePanel
              className="h-full"
              botName={settings.bot_name}
              greeting={settings.voice_greeting}
              maxSeconds={settings.voice_max_session_seconds}
              onBack={() => setVoice(false)}
              onClose={() => { setVoice(false); setOpen(false) }}
            />
          )}
        </div>
      )}
      {voiceOn && !open && (
        <button
          onClick={openVoice}
          aria-label="Sesli asistanla konuş"
          title="Sesli asistan"
          className="fixed z-40 bottom-[5.6rem] right-5 sm:bottom-24 sm:right-[1.65rem] w-11 h-11 rounded-full bg-navy-900 text-gold-200 border border-gold-400/70 shadow-lg hover:bg-navy-700 hover:scale-105 transition flex items-center justify-center"
        >
          <Mic size={19} />
        </button>
      )}
      <button
        onClick={toggle}
        aria-label={open ? 'Sohbeti kapat' : 'Sohbeti aç'}
        className={`fixed z-40 bottom-5 right-5 sm:bottom-6 sm:right-6 w-14 h-14 rounded-full bg-gradient-to-br from-gold-300 via-gold-500 to-gold-600 text-white shadow-xl shadow-gold-600/30 hover:brightness-110 hover:scale-105 transition flex items-center justify-center ${open ? 'hidden sm:flex' : ''}`}
      >
        {open ? <X size={24} /> : <MessageCircle size={26} />}
        {!open && <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-aegean-500 border-2 border-white" />}
      </button>
    </>
  )
}
