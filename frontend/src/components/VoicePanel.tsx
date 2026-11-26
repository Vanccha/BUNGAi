import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, Keyboard, Loader2, Mic, MicOff, PhoneOff, Send, X } from 'lucide-react'
import { useVoiceAssistant, type VoiceStatus } from '../lib/useVoiceAssistant'
import { PaymentCard, SummaryCard } from './ChatPanel'

const STATUS_LABEL: Record<VoiceStatus, string> = {
  idle: 'Hazır',
  connecting: 'Bağlanıyor…',
  listening: 'Dinliyorum',
  thinking: 'Düşünüyorum…',
  speaking: 'Konuşuyorum',
  ended: 'Görüşme bitti',
  error: 'Bağlantı kurulamadı',
}

const mmss = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

/** Mikrofon/asistan ses seviyesine göre nefes alan küre. Seviye React state'i değil ref'tir (60 fps, yeniden render yok). */
function Orb({ status, levels }: { status: VoiceStatus; levels: React.RefObject<{ mic: number; out: number }> }) {
  const core = useRef<HTMLDivElement>(null)
  const ring1 = useRef<HTMLDivElement>(null)
  const ring2 = useRef<HTMLDivElement>(null)
  useEffect(() => {
    let raf = 0
    let smooth = 0
    const tick = () => {
      const { mic, out } = levels.current
      const target = status === 'speaking' ? out : status === 'listening' ? mic : status === 'thinking' ? 0.12 : 0.05
      smooth += (target - smooth) * 0.25
      if (core.current) core.current.style.transform = `scale(${1 + smooth * 0.35})`
      if (ring1.current) { ring1.current.style.transform = `scale(${1.15 + smooth * 0.7})`; ring1.current.style.opacity = String(0.15 + smooth * 0.5) }
      if (ring2.current) { ring2.current.style.transform = `scale(${1.35 + smooth * 1.0})`; ring2.current.style.opacity = String(0.08 + smooth * 0.3) }
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => cancelAnimationFrame(raf)
  }, [status, levels])

  const palette =
    status === 'speaking' ? 'from-gold-200 via-gold-400 to-gold-600'
    : status === 'listening' ? 'from-pool-200 via-aegean-500 to-navy-600'
    : status === 'thinking' || status === 'connecting' ? 'from-gold-100 via-gold-300 to-aegean-500'
    : status === 'error' ? 'from-red-200 via-red-400 to-red-600'
    : 'from-navy-200 via-navy-400 to-navy-700'
  const ringColor = status === 'speaking' ? 'bg-gold-400' : 'bg-aegean-500'
  return (
    <div className="relative w-40 h-40 flex items-center justify-center" aria-hidden>
      <div ref={ring2} className={`absolute inset-6 rounded-full ${ringColor} transition-colors duration-500`} />
      <div ref={ring1} className={`absolute inset-6 rounded-full ${ringColor} transition-colors duration-500`} />
      <div
        ref={core}
        className={`relative w-24 h-24 rounded-full bg-gradient-to-br ${palette} shadow-xl shadow-navy-900/20 transition-colors duration-500 ${status === 'thinking' || status === 'connecting' ? 'animate-pulse' : ''}`}
      >
        <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white/50 to-transparent" />
      </div>
    </div>
  )
}

export function VoicePanel({
  botName, greeting, maxSeconds, onBack, onClose, className = '',
}: {
  botName: string
  greeting: string
  maxSeconds: number
  onBack: () => void
  onClose: () => void
  className?: string
}) {
  const v = useVoiceAssistant({ maxSeconds, greeting })
  const [text, setText] = useState('')
  const [showType, setShowType] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const live = v.status === 'listening' || v.status === 'thinking' || v.status === 'speaking'
  const busy = v.status === 'connecting'
  const idle = v.status === 'idle' || v.status === 'ended' || v.status === 'error'
  const remaining = Math.max(0, v.maxSeconds - v.elapsed)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [v.msgs, v.actions])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (v.sendText(text)) setText('')
  }
  const back = () => { if (live || busy) v.end(); onBack() }
  const close = () => { if (live || busy) v.end(); onClose() }

  return (
    <div className={`flex flex-col bg-pool-50 ${className}`}>
      <div className="flex items-center gap-3 bg-gradient-to-r from-navy-900 to-navy-700 text-white border-b-2 border-gold-500 px-4 py-3 shrink-0">
        <button onClick={back} aria-label="Yazılı sohbete dön" title="Yazılı sohbete dön" className="p-1.5 -ml-1 rounded-full hover:bg-white/15"><ArrowLeft size={20} /></button>
        <div className="flex-1 min-w-0">
          <div className="font-semibold leading-tight truncate">{botName} · Sesli asistan</div>
          <div className="text-xs text-navy-200">{live ? `${mmss(v.elapsed)} / ${mmss(v.maxSeconds)}` : 'Konuşarak rezervasyon ve bilgi alın'}</div>
        </div>
        <button onClick={close} aria-label="Kapat" className="p-1.5 rounded-full hover:bg-white/15"><X size={20} /></button>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 px-4 pt-4 pb-2 flex flex-col">
        <div className="flex flex-col items-center shrink-0">
          <Orb status={v.status} levels={v.levels} />
          <div role="status" aria-live="polite" className="mt-1 text-sm font-semibold text-navy-800 flex items-center gap-2">
            {busy && <Loader2 size={14} className="animate-spin" />}
            {STATUS_LABEL[v.status]}
          </div>
          {live && remaining <= 30 && (
            <div className="mt-1 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-3 py-0.5">Görüşme {remaining} saniye içinde sona erecek</div>
          )}
          {v.muted && live && <div className="mt-1 text-xs text-red-700">Mikrofonunuz kapalı</div>}
        </div>

        {v.error && (
          <div role="alert" className="mt-3 rounded-2xl bg-red-50 border border-red-200 text-red-800 px-3.5 py-2.5 text-sm">{v.error}</div>
        )}
        {v.endReason && !v.error && (
          <div className="mt-3 text-center text-xs text-stone-500">{v.endReason}</div>
        )}

        <div className="mt-3 space-y-2 flex-1">
          {v.msgs.slice(-8).map(m => (
            <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : ''}`}>
              <div className={`max-w-[88%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed break-words ${
                m.role === 'user' ? 'rounded-tr-sm bg-navy-800 text-white' : 'rounded-tl-sm bg-white border border-navy-100 shadow-sm text-slate-800'
              } ${m.final ? '' : 'opacity-80'}`}>
                {m.text || <span className="opacity-60">…</span>}
              </div>
            </div>
          ))}
          {v.actions.map((a, i) => (
            <div key={i} className="max-w-[92%]">
              {a.type === 'payment_link' ? <PaymentCard a={a} /> : <SummaryCard r={a.reservation} />}
            </div>
          ))}
          <div ref={endRef} />
        </div>
      </div>

      <div className="shrink-0 border-t border-navy-100 bg-white p-3 space-y-2">
        {live && showType && (
          <form onSubmit={submit} className="flex items-center gap-2">
            <input
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="E-postanızı veya mesajınızı buraya yazın…"
              aria-label="Yazılı mesaj"
              autoFocus
              className="input !rounded-full"
            />
            <button type="submit" disabled={!text.trim()} className="btn btn-primary !p-3 !rounded-full" aria-label="Gönder"><Send size={16} /></button>
          </form>
        )}
        <div className="flex items-center justify-center gap-3">
          {idle || busy ? (
            <button onClick={v.start} disabled={busy} className="btn btn-primary !px-6 !py-3 text-base">
              {busy ? <Loader2 size={18} className="animate-spin" /> : <Mic size={18} />}
              {v.status === 'ended' || v.status === 'error' ? 'Yeniden başlat' : 'Konuşmaya başla'}
            </button>
          ) : (
            <>
              <button
                onClick={v.toggleMute}
                aria-pressed={v.muted}
                aria-label={v.muted ? 'Mikrofonu aç' : 'Mikrofonu kapat'}
                title={v.muted ? 'Mikrofonu aç' : 'Mikrofonu kapat'}
                className={`w-12 h-12 rounded-full flex items-center justify-center border transition ${v.muted ? 'bg-red-50 border-red-300 text-red-700' : 'bg-white border-navy-200 text-navy-800 hover:bg-navy-50'}`}
              >
                {v.muted ? <MicOff size={20} /> : <Mic size={20} />}
              </button>
              <button onClick={v.end} aria-label="Görüşmeyi bitir" title="Görüşmeyi bitir" className="w-14 h-14 rounded-full bg-red-600 hover:bg-red-700 text-white flex items-center justify-center shadow-lg"><PhoneOff size={22} /></button>
              <button
                onClick={() => setShowType(s => !s)}
                aria-pressed={showType}
                aria-label="Yazarak gönder"
                title="Yazarak gönder"
                className={`w-12 h-12 rounded-full flex items-center justify-center border transition ${showType ? 'bg-gold-50 border-gold-400 text-gold-700' : 'bg-white border-navy-200 text-navy-800 hover:bg-navy-50'}`}
              >
                <Keyboard size={20} />
              </button>
            </>
          )}
        </div>
        {idle && v.status === 'idle' && (
          <p className="text-[11px] text-center text-stone-500">Mikrofon izni istenecek. Görüşme en fazla {Math.max(1, Math.round(maxSeconds / 60))} dakika sürer. Kart bilgilerinizi sesle paylaşmayın.</p>
        )}
      </div>
    </div>
  )
}
