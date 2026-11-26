import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { ChatAction } from '../api/types'

/**
 * Sesli asistan istemcisi (OpenAI Realtime, WebRTC).
 *
 * Akış:
 *  1) Mikrofon izni al.
 *  2) Backend'den geçici anahtar al (POST /api/voice/session). Talimatlar/araçlar sunucuda sabitlenmiştir.
 *  3) RTCPeerConnection kur: mikrofon parçası + "oai-events" veri kanalı; SDP teklifini OpenAI'ye gönder
 *     (POST https://api.openai.com/v1/realtime/calls, Bearer = geçici anahtar). Yanıttaki `Location` başlığı çağrı kimliğidir.
 *  4) Çağrı kimliğini backend'e bildir (attach): backend aynı çağrıya bir WebSocket (yan kanal) açar ve araçları
 *     sunucuda çalıştırır. Tarayıcı araç çağrılarına karışmaz; yalnızca kartları (actions) çeker.
 *  5) Veri kanalından gelen olaylarla durum + canlı döküm güncellenir.
 */

export type VoiceStatus = 'idle' | 'connecting' | 'listening' | 'thinking' | 'speaking' | 'ended' | 'error'

export interface VoiceMsg { id: string; role: 'user' | 'assistant'; text: string; final: boolean }

const REALTIME_CALLS_URL = 'https://api.openai.com/v1/realtime/calls'

function friendlyError(e: unknown): string {
  if (e instanceof DOMException) {
    if (e.name === 'NotAllowedError' || e.name === 'SecurityError')
      return 'Mikrofon izni verilmedi. Tarayıcı adres çubuğundaki kilit simgesinden mikrofona izin verip tekrar deneyin.'
    if (e.name === 'NotFoundError' || e.name === 'OverconstrainedError')
      return 'Mikrofon bulunamadı. Bir mikrofon bağlayıp tekrar deneyin.'
    if (e.name === 'NotReadableError') return 'Mikrofon başka bir uygulama tarafından kullanılıyor olabilir.'
  }
  if (e instanceof ApiError) return e.message
  if (e instanceof Error && e.message) return e.message
  return 'Sesli görüşme başlatılamadı. Lütfen tekrar deneyin.'
}

export function voiceSupported(): boolean {
  return typeof window !== 'undefined' && 'RTCPeerConnection' in window && !!navigator.mediaDevices?.getUserMedia
}

/** Geliştirme/test anahtarı: localStorage.bungai_fake_mic = '1' ise gerçek mikrofon yerine sessiz yapay akış kullanılır. */
function fakeMicStream(ctx: AudioContext): MediaStream {
  const dest = ctx.createMediaStreamDestination()
  const osc = ctx.createOscillator()
  const g = ctx.createGain()
  g.gain.value = 0
  osc.connect(g).connect(dest)
  osc.start()
  return dest.stream
}

export function useVoiceAssistant(opts: { maxSeconds: number; greeting: string }) {
  const [status, setStatus] = useState<VoiceStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [msgs, setMsgs] = useState<VoiceMsg[]>([])
  const [actions, setActions] = useState<ChatAction[]>([])
  const [elapsed, setElapsed] = useState(0)
  const [muted, setMuted] = useState(false)
  const [endReason, setEndReason] = useState<string | null>(null)
  const [maxSeconds, setMaxSeconds] = useState(opts.maxSeconds)
  const levels = useRef({ mic: 0, out: 0 })

  const r = useRef({
    pc: null as RTCPeerConnection | null,
    dc: null as RTCDataChannel | null,
    stream: null as MediaStream | null,
    audioEl: null as HTMLAudioElement | null,
    ctx: null as AudioContext | null,
    sessionId: null as string | null,
    maxSeconds: opts.maxSeconds,
    timer: 0 as number,
    poll: 0 as number,
    raf: 0 as number,
    actionsSeen: 0,
    active: false,
    speaking: false,
    startedAt: 0,
    items: new Map<string, string>(), // item_id -> msg id (kullanıcı)
  })
  const optsRef = useRef(opts)
  optsRef.current = opts

  const stopAll = useCallback((finalStatus: VoiceStatus, reason?: string) => {
    const s = r.current
    const wasActive = s.active
    s.active = false
    window.clearInterval(s.timer)
    window.clearInterval(s.poll)
    cancelAnimationFrame(s.raf)
    try { s.dc?.close() } catch { /* yoksay */ }
    try { s.pc?.getSenders().forEach(x => x.track?.stop()) } catch { /* yoksay */ }
    try { s.pc?.close() } catch { /* yoksay */ }
    s.stream?.getTracks().forEach(t => t.stop())
    if (s.audioEl) { s.audioEl.srcObject = null; s.audioEl = null }
    try { void s.ctx?.close() } catch { /* yoksay */ }
    s.pc = s.dc = s.stream = s.ctx = null
    levels.current = { mic: 0, out: 0 }
    if (s.sessionId && wasActive) {
      // Son kartları da al ve backend'e görüşmenin bittiğini bildir.
      const sid = s.sessionId
      api.voice.actions(sid, s.actionsSeen).then(a => { s.actionsSeen = a.next; if (a.actions.length) setActions(p => [...p, ...a.actions]) }).catch(() => {})
        .finally(() => { api.voice.end(sid).catch(() => {}) })
    }
    setMsgs(m => m.map(x => ({ ...x, final: true })).filter(x => x.text.trim() !== ''))
    if (reason) setEndReason(reason)
    setStatus(finalStatus)
  }, [])

  const fail = useCallback((e: unknown) => {
    setError(friendlyError(e))
    stopAll('error')
  }, [stopAll])

  const upsert = useCallback((id: string, role: VoiceMsg['role'], fn: (prev: string) => string, final?: boolean) => {
    setMsgs(list => {
      const i = list.findIndex(m => m.id === id)
      if (i < 0) return [...list, { id, role, text: fn(''), final: !!final }]
      const copy = list.slice()
      copy[i] = { ...copy[i], text: fn(copy[i].text), final: final ?? copy[i].final }
      return copy
    })
  }, [])

  const handleEvent = useCallback((ev: Record<string, any>) => { // eslint-disable-line @typescript-eslint/no-explicit-any
    const s = r.current
    switch (ev.type) {
      case 'input_audio_buffer.speech_started':
        setStatus('listening'); break
      case 'input_audio_buffer.speech_stopped':
      case 'input_audio_buffer.committed':
        setStatus('thinking'); break
      case 'response.created':
        setStatus(st => (st === 'listening' || st === 'connecting' ? 'thinking' : st)); break
      case 'output_audio_buffer.started':
        s.speaking = true; setStatus('speaking'); break
      case 'output_audio_buffer.stopped':
      case 'output_audio_buffer.cleared':
        s.speaking = false; setStatus('listening'); break
      case 'conversation.item.added':
      case 'conversation.item.created': {
        const it = ev.item
        if (it?.type === 'message' && it.role === 'user') {
          const typed = (it.content ?? []).filter((c: any) => c.type === 'input_text').map((c: any) => c.text).join(' ') // eslint-disable-line @typescript-eslint/no-explicit-any
          const id = 'u_' + it.id
          s.items.set(it.id, id)
          upsert(id, 'user', () => typed, !!typed)
        }
        break
      }
      case 'conversation.item.input_audio_transcription.completed': {
        const id = s.items.get(ev.item_id) ?? 'u_' + ev.item_id
        upsert(id, 'user', () => String(ev.transcript ?? '').trim(), true)
        break
      }
      case 'response.output_audio_transcript.delta':
        upsert('a_' + ev.response_id + '_' + ev.item_id, 'assistant', p => p + (ev.delta ?? ''), false)
        if (!s.speaking) { s.speaking = true; setStatus('speaking') }
        break
      case 'response.output_audio_transcript.done':
        upsert('a_' + ev.response_id + '_' + ev.item_id, 'assistant', () => String(ev.transcript ?? ''), true)
        break
      case 'response.function_call_arguments.done':
        setStatus('thinking')
        break
      case 'response.done': {
        const out = ev.response?.output ?? []
        if (out.some((o: any) => o.type === 'function_call')) setStatus('thinking') // eslint-disable-line @typescript-eslint/no-explicit-any
        else if (!s.speaking) setStatus('listening')
        break
      }
      case 'error': {
        const code = ev.error?.code
        if (code === 'session_expired' || code === 'max_duration') fail(new Error('Görüşme süresi doldu.'))
        break
      }
    }
  }, [fail, upsert])

  const start = useCallback(async () => {
    const s = r.current
    if (s.active) return
    setError(null); setEndReason(null); setMsgs([]); setActions([]); setElapsed(0); setMuted(false)
    s.actionsSeen = 0; s.items.clear(); s.speaking = false
    if (!voiceSupported()) {
      setError('Bu tarayıcı sesli görüşmeyi desteklemiyor. Lütfen Chrome, Edge, Safari veya Firefox\'un güncel bir sürümünü kullanın (HTTPS gerekir).')
      setStatus('error'); return
    }
    setStatus('connecting')
    s.active = true
    try {
      const ctx = new AudioContext()
      s.ctx = ctx
      if (ctx.state === 'suspended') void ctx.resume().catch(() => {}) // await ETME: kullanıcı etkileşimi yoksa söz hiç çözülmeyebilir
      let stream: MediaStream
      let fake = false
      try { fake = localStorage.getItem('bungai_fake_mic') === '1' } catch { /* yoksay */ }
      stream = fake
        ? fakeMicStream(ctx)
        : await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 } })
      s.stream = stream

      const session = await api.voice.createSession()
      if (!s.active) return
      s.sessionId = session.session_id
      s.maxSeconds = session.max_seconds || optsRef.current.maxSeconds
      setMaxSeconds(s.maxSeconds)

      const pc = new RTCPeerConnection()
      s.pc = pc
      pc.onconnectionstatechange = () => {
        if (!s.active) return
        if (pc.connectionState === 'failed') fail(new Error('Bağlantı koptu. İnternet bağlantınızı kontrol edip tekrar deneyin.'))
        else if (pc.connectionState === 'disconnected') window.setTimeout(() => {
          if (s.active && pc.connectionState === 'disconnected') fail(new Error('Bağlantı koptu. İnternet bağlantınızı kontrol edip tekrar deneyin.'))
        }, 4000)
      }

      // Asistan sesi
      const audioEl = new Audio()
      audioEl.autoplay = true
      s.audioEl = audioEl
      const micAn = ctx.createAnalyser(); micAn.fftSize = 512
      const outAn = ctx.createAnalyser(); outAn.fftSize = 512
      ctx.createMediaStreamSource(stream).connect(micAn)
      pc.ontrack = e => {
        audioEl.srcObject = e.streams[0]
        ctx.createMediaStreamSource(e.streams[0]).connect(outAn) // yalnızca analiz; çıkış <audio> öğesinden
      }
      stream.getAudioTracks().forEach(t => pc.addTrack(t, stream))

      const dc = pc.createDataChannel('oai-events')
      s.dc = dc
      dc.onmessage = m => { try { handleEvent(JSON.parse(m.data)) } catch { /* yoksay */ } }
      dc.onopen = () => {
        if (!s.active) return
        s.startedAt = Date.now()
        setStatus('listening')
        const g = (session.greeting || optsRef.current.greeting || '').trim()
        if (g) dc.send(JSON.stringify({ type: 'response.create', response: { instructions: `Misafiri şu cümlelerle karşıla, başka bir şey ekleme: ${g}` } }))
      }

      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      let res: Response
      try {
        res = await fetch(REALTIME_CALLS_URL, {
          method: 'POST',
          body: offer.sdp,
          headers: { Authorization: `Bearer ${session.client_secret}`, 'Content-Type': 'application/sdp' },
        })
      } catch {
        throw new Error('Ses sunucusuna ulaşılamadı. İnternet bağlantınızı kontrol edin.')
      }
      if (!res.ok) {
        throw new Error(res.status === 401 || res.status === 403
          ? 'Oturum anahtarının süresi doldu. Lütfen görüşmeyi yeniden başlatın.'
          : 'Ses bağlantısı kurulamadı. Lütfen tekrar deneyin.')
      }
      const callId = res.headers.get('Location')?.split('/').pop() ?? ''
      const answer = await res.text()
      await pc.setRemoteDescription({ type: 'answer', sdp: answer })
      if (!s.active) return
      if (!callId) throw new Error('Ses bağlantısı kurulamadı (çağrı kimliği alınamadı).')
      await api.voice.attach(session.session_id, callId)

      // Süre sayacı + otomatik kapanış
      s.timer = window.setInterval(() => {
        const sec = Math.floor((Date.now() - (s.startedAt || Date.now())) / 1000)
        setElapsed(s.startedAt ? sec : 0)
        if (s.startedAt && sec >= s.maxSeconds) stopAll('ended', 'Görüşme süre sınırına ulaştı.')
      }, 500)
      // Araç sonuçlarından doğan kartları çek
      s.poll = window.setInterval(async () => {
        if (!s.sessionId) return
        try {
          const a = await api.voice.actions(s.sessionId, s.actionsSeen)
          s.actionsSeen = a.next
          if (a.actions.length) setActions(p => [...p, ...a.actions])
        } catch { /* geçici hata */ }
      }, 1000)
      // Seviye ölçer (turuncu/altın küre için)
      const buf = new Uint8Array(256)
      const rms = (an: AnalyserNode) => {
        an.getByteTimeDomainData(buf)
        let sum = 0
        for (let i = 0; i < buf.length; i++) { const v = (buf[i] - 128) / 128; sum += v * v }
        return Math.min(1, Math.sqrt(sum / buf.length) * 3.2)
      }
      const loop = () => {
        levels.current.mic = rms(micAn)
        levels.current.out = rms(outAn)
        s.raf = requestAnimationFrame(loop)
      }
      loop()
    } catch (e) {
      if (s.active) fail(e)
    }
  }, [fail, handleEvent, stopAll])

  const end = useCallback(() => stopAll('ended', 'Görüşme sona erdi.'), [stopAll])

  const toggleMute = useCallback(() => {
    const s = r.current
    const next = !s.stream?.getAudioTracks()[0]?.enabled
    s.stream?.getAudioTracks().forEach(t => { t.enabled = next })
    setMuted(!next)
  }, [])

  const sendText = useCallback((text: string) => {
    const dc = r.current.dc
    const t = text.trim()
    if (!t || !dc || dc.readyState !== 'open') return false
    dc.send(JSON.stringify({ type: 'conversation.item.create', item: { type: 'message', role: 'user', content: [{ type: 'input_text', text: t }] } }))
    dc.send(JSON.stringify({ type: 'response.create' }))
    setStatus('thinking')
    return true
  }, [])

  // Bileşen kapanınca/sayfa değişince her şeyi temizle
  useEffect(() => {
    const s = r.current
    const onUnload = () => { if (s.sessionId && s.active) navigator.sendBeacon?.(`/api/voice/session/${s.sessionId}/end`) }
    window.addEventListener('pagehide', onUnload)
    return () => { window.removeEventListener('pagehide', onUnload); if (s.active) stopAll('idle') }
  }, [stopAll])

  return { status, error, msgs, actions, elapsed, muted, endReason, levels, maxSeconds, start, end, toggleMute, sendText }
}
