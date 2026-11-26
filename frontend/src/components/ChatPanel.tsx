import { useEffect, useRef, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { Bot, CalendarCheck, ChevronRight, CreditCard, Mic, RotateCcw, Search, Send, X } from 'lucide-react'
import type { AdminChatResponse, ChatAction, Reservation, SearchTrace } from '../api/types'
import { errMsg, fmtDate, store, tl } from '../lib/format'
import { StatusBadge } from './ui'

interface Msg { role: 'user' | 'bot' | 'error'; text: string; actions?: ChatAction[]; searches?: SearchTrace[] }

export const QUICK_REPLIES = ['Müsaitlik sorgula', 'Fiyatlar nedir?', 'Evcil hayvan kabul ediyor musunuz?', 'Rezervasyon yapmak istiyorum']

function Md({ text }: { text: string }) {
  return (
    <div className="chat-md text-sm leading-relaxed [&_p]:mb-2 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:mb-0.5 [&_strong]:font-semibold">
      <ReactMarkdown
        components={{
          a: ({ href, children }) =>
            href && href.startsWith('/') ? (
              <Link to={href} className="underline font-medium">{children}</Link>
            ) : (
              <a href={href} target="_blank" rel="noopener noreferrer" className="underline font-medium">{children}</a>
            ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  )
}

function Sources({ searches }: { searches: SearchTrace[] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-1.5 text-xs">
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1 text-navy-600 hover:text-navy-900 font-semibold">
        <ChevronRight size={14} className={`transition ${open ? 'rotate-90' : ''}`} />
        <Search size={12} />Kaynaklar ({searches.length} arama)
      </button>
      {open && (
        <div className="mt-1.5 space-y-2">
          {searches.map((t, i) => (
            <div key={i} className="rounded-xl border border-navy-100 bg-white p-2.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-navy-800">&ldquo;{t.query}&rdquo;</span>
                {t.below_threshold && <span className="rounded-full bg-amber-100 text-amber-800 px-2 py-0.5 font-semibold">Eşik altı: güvenilir sonuç yok</span>}
              </div>
              {t.results.length === 0 ? <p className="text-stone-500 mt-1">Sonuç yok.</p> : (
                <ul className="mt-1.5 space-y-1">
                  {t.results.slice(0, 5).map((h, j) => (
                    <li key={j} className="flex justify-between gap-2 text-navy-700">
                      <span className="truncate">{h.entry_title} <span className="text-stone-400">· {h.category}</span></span>
                      <span className="font-mono text-stone-500 shrink-0">{h.fused_score.toFixed(3)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function PaymentCard({ a }: { a: Extract<ChatAction, { type: 'payment_link' }> }) {
  const nav = useNavigate()
  const go = () => {
    if (a.url.startsWith('/')) nav(a.url)
    else {
      try {
        const u = new URL(a.url)
        if (u.origin === window.location.origin) nav(u.pathname + u.search)
        else window.location.href = a.url
      } catch { window.location.href = a.url }
    }
  }
  return (
    <div className="mt-2 rounded-2xl bg-gradient-to-br from-navy-800 to-navy-900 text-white p-4 ring-1 ring-gold-400/50 shadow-lg">
      <div className="flex items-center gap-2 text-xs text-navy-200"><CreditCard size={14} /> Rezervasyon {a.reservation_code}</div>
      <div className="font-display text-2xl mt-1">{tl(a.amount)}</div>
      <button onClick={go} className="btn btn-primary w-full mt-3">Ödemeye Geç</button>
    </div>
  )
}

export function SummaryCard({ r }: { r: Reservation }) {
  return (
    <div className="mt-2 rounded-2xl border border-navy-200 bg-white p-3 text-slate-800 text-xs space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 font-semibold text-navy-800"><CalendarCheck size={14} />{r.bungalow_name}</span>
        <StatusBadge status={r.status} />
      </div>
      <div className="text-stone-600">{fmtDate(r.check_in)} – {fmtDate(r.check_out)} · {r.nights} gece · {r.guests} kişi</div>
      <div className="flex justify-between items-center pt-1">
        <span className="font-mono text-stone-500">{r.code}</span>
        <span className="font-semibold text-navy-800">{tl(r.total_price)}</span>
      </div>
      <Link to={`/rezervasyon/${r.code}`} className="block text-navy-700 underline pt-0.5">Rezervasyonu görüntüle</Link>
    </div>
  )
}

export function ChatPanel({
  send, botName, welcome, storageKey, onClose, onVoice, quick = true, className = '',
}: {
  send: (message: string, sessionId?: string) => Promise<AdminChatResponse>
  botName: string
  welcome: string
  storageKey: string
  onClose?: () => void
  onVoice?: () => void   // verilirse başlıkta mikrofon (sesli mod) düğmesi gösterilir
  quick?: boolean
  className?: string
}) {
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const sid = useRef<string | undefined>(store.get(storageKey) ?? undefined)
  const histKey = storageKey + '_history'
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Önceki konuşmayı geri yükle
  useEffect(() => {
    try {
      const h = store.get(histKey)
      if (h && sid.current) setMsgs(JSON.parse(h) as Msg[])
    } catch { /* yoksay */ }
  }, [histKey])
  useEffect(() => {
    if (msgs.length) store.set(histKey, JSON.stringify(msgs.slice(-60)))
  }, [msgs, histKey])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [msgs, busy])
  useEffect(() => { if (!busy) inputRef.current?.focus() }, [busy])

  const submit = async (text: string) => {
    const t = text.trim()
    if (!t || busy) return
    setInput('')
    setMsgs(m => [...m, { role: 'user', text: t }])
    setBusy(true)
    try {
      const r = await send(t, sid.current)
      sid.current = r.session_id
      store.set(storageKey, r.session_id)
      setMsgs(m => [...m, { role: 'bot', text: r.reply, actions: r.actions, searches: r.debug?.searches }])
    } catch (e) {
      setMsgs(m => [...m, { role: 'error', text: errMsg(e) }])
    } finally { setBusy(false) }
  }

  const reset = () => {
    sid.current = undefined
    store.del(storageKey); store.del(histKey)
    setMsgs([])
  }

  return (
    <div className={`flex flex-col bg-pool-50 ${className}`}>
      <div className="flex items-center gap-3 bg-gradient-to-r from-navy-900 to-navy-700 text-white border-b-2 border-gold-500 px-4 py-3 shrink-0">
        <div className="w-9 h-9 rounded-full bg-gold-400/25 text-gold-200 flex items-center justify-center"><Bot size={20} /></div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold leading-tight truncate">{botName}</div>
          <div className="text-xs text-navy-200 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-300" />Çevrimiçi</div>
        </div>
        {onVoice && (
          <button onClick={onVoice} title="Sesli asistan" aria-label="Sesli asistanla konuş" className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-full bg-gold-400/90 text-navy-900 font-semibold hover:bg-gold-300"><Mic size={14} />Sesli</button>
        )}
        <button onClick={reset} title="Yeni sohbet" className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-full bg-white/10 hover:bg-white/20"><RotateCcw size={13} />Yeni sohbet</button>
        {onClose && <button onClick={onClose} aria-label="Kapat" className="p-1.5 rounded-full hover:bg-white/15"><X size={20} /></button>}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 min-h-0">
        <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white border border-navy-100 px-3.5 py-2.5 shadow-sm"><Md text={welcome} /></div>
        {msgs.length === 0 && quick && (
          <div className="flex flex-wrap gap-2 pt-1">
            {QUICK_REPLIES.map(q => (
              <button key={q} onClick={() => submit(q)} className="text-xs rounded-full border border-gold-300 text-navy-800 bg-white px-3 py-1.5 hover:bg-gold-50 transition">{q}</button>
            ))}
          </div>
        )}
        {msgs.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-navy-800 text-white px-3.5 py-2.5 text-sm whitespace-pre-wrap break-words">{m.text}</div>
            </div>
          ) : m.role === 'error' ? (
            <div key={i} className="max-w-[90%] rounded-2xl bg-red-50 border border-red-200 text-red-800 px-3.5 py-2.5 text-sm">{m.text}</div>
          ) : (
            <div key={i} className="max-w-[88%]">
              <div className="rounded-2xl rounded-tl-sm bg-white border border-navy-100 px-3.5 py-2.5 shadow-sm break-words"><Md text={m.text} /></div>
              {m.searches && m.searches.length > 0 && <Sources searches={m.searches} />}
              {m.actions?.map((a, j) => a.type === 'payment_link' ? <PaymentCard key={j} a={a} /> : <SummaryCard key={j} r={a.reservation} />)}
            </div>
          ),
        )}
        {busy && (
          <div className="inline-flex gap-1 rounded-2xl rounded-tl-sm bg-white border border-navy-100 px-4 py-3 shadow-sm" aria-label="Yazıyor">
            {[0, 1, 2].map(i => <span key={i} className="dot w-1.5 h-1.5 rounded-full bg-gold-500" style={{ animationDelay: `${i * 0.18}s` }} />)}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={e => { e.preventDefault(); submit(input) }} className="flex items-end gap-2 p-3 border-t border-navy-100 bg-white shrink-0">
        <textarea
          ref={inputRef}
          rows={1}
          value={input}
          disabled={busy}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(input) } }}
          placeholder="Mesajınızı yazın…"
          className="input !rounded-2xl resize-none max-h-28 disabled:opacity-60"
        />
        <button type="submit" disabled={busy || !input.trim()} className="btn btn-primary !p-3 !rounded-full" aria-label="Gönder"><Send size={18} /></button>
      </form>
    </div>
  )
}
