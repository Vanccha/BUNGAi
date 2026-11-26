import type {
  AdminStats, Availability, Bungalow, CardData, ChatResponse, KnowledgeEntry, PaymentInfo,
  PaymentInit, PaymentResult, VoiceSessionInfo, VoiceActionsResponse, VoiceSessionListItem, VoiceSessionDetail, AdminChatResponse, KnowledgeInput, RagStats, SearchTrace, PublicSettings, Reservation, ReservationCreate, ReservationStatus, Settings,
} from './types'

const TOKEN_KEY = 'bungai_admin_token'

export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}
export function setToken(t: string | null) {
  try { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY) } catch { /* yoksay */ }
}

let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(fn: (() => void) | null) { onUnauthorized = fn }

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

async function request<T>(method: string, path: string, body?: unknown, auth = false): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth) { const t = getToken(); if (t) headers.Authorization = `Bearer ${t}` }
  let res: Response
  try {
    res = await fetch(path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined })
  } catch {
    throw new ApiError('Sunucuya ulaşılamadı. Lütfen bağlantınızı kontrol edin.', 0)
  }
  if (!res.ok) {
    let msg = `Bir hata oluştu (${res.status})`
    try {
      const j = await res.json()
      if (typeof j.detail === 'string') msg = j.detail
      else if (Array.isArray(j.detail) && j.detail[0]?.msg) msg = j.detail.map((d: { msg: string }) => d.msg).join(', ')
    } catch { /* yoksay */ }
    if (res.status === 401 && auth) onUnauthorized?.()
    throw new ApiError(msg, res.status)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

const qs = (o: Record<string, string | number | undefined>) =>
  '?' + Object.entries(o).filter(([, v]) => v !== undefined && v !== '').map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&')

export const api = {
  settings: () => request<PublicSettings>('GET', '/api/settings/public'),
  bungalows: () => request<Bungalow[]>('GET', '/api/bungalows'),
  bungalow: (slug: string) => request<Bungalow>('GET', `/api/bungalows/${slug}`),
  availability: (bungalow_id: number, check_in: string, check_out: string) =>
    request<Availability>('GET', '/api/availability' + qs({ bungalow_id, check_in, check_out })),
  calendar: (bungalow_id: number, month: string) =>
    request<{ booked_dates: string[] }>('GET', '/api/availability/calendar' + qs({ bungalow_id, month })),
  createReservation: (b: ReservationCreate) => request<Reservation>('POST', '/api/reservations', b),
  reservation: (code: string) => request<Reservation>('GET', `/api/reservations/${code}`),
  initPayment: (reservation_code: string) => request<PaymentInit>('POST', '/api/payments/init', { reservation_code }),
  payment: (token: string) => request<PaymentInfo>('GET', `/api/payments/${token}`),
  completePayment: (token: string, c: CardData) => request<PaymentResult>('POST', `/api/payments/${token}/complete`, c),
  chat: (message: string, session_id?: string) => request<ChatResponse>('POST', '/api/chat', { session_id, message }),
  voice: {
    createSession: () => request<VoiceSessionInfo>('POST', '/api/voice/session'),
    attach: (sessionId: string, call_id: string) => request<{ ok: boolean }>('POST', `/api/voice/session/${sessionId}/attach`, { call_id }),
    actions: (sessionId: string, after: number) => request<VoiceActionsResponse>('GET', `/api/voice/session/${sessionId}/actions?after=${after}`),
    end: (sessionId: string) => request<{ ok: boolean }>('POST', `/api/voice/session/${sessionId}/end`),
  },

  admin: {
    login: (username: string, password: string) =>
      request<{ access_token: string; token_type: string }>('POST', '/api/admin/login', { username, password }),
    me: () => request<{ username: string }>('GET', '/api/admin/me', undefined, true),
    getSettings: () => request<Settings>('GET', '/api/admin/settings', undefined, true),
    saveSettings: (s: Settings) => request<Settings>('PUT', '/api/admin/settings', s, true),
    knowledge: () => request<KnowledgeEntry[]>('GET', '/api/admin/knowledge', undefined, true),
    createKnowledge: (k: KnowledgeInput) => request<KnowledgeEntry>('POST', '/api/admin/knowledge', k, true),
    updateKnowledge: (id: number, k: KnowledgeInput) => request<KnowledgeEntry>('PUT', `/api/admin/knowledge/${id}`, k, true),
    deleteKnowledge: (id: number) => request<void>('DELETE', `/api/admin/knowledge/${id}`, undefined, true),
    bungalows: () => request<Bungalow[]>('GET', '/api/admin/bungalows', undefined, true),
    createBungalow: (b: Omit<Bungalow, 'id'>) => request<Bungalow>('POST', '/api/admin/bungalows', b, true),
    updateBungalow: (id: number, b: Omit<Bungalow, 'id'>) => request<Bungalow>('PUT', `/api/admin/bungalows/${id}`, b, true),
    deleteBungalow: (id: number) => request<void>('DELETE', `/api/admin/bungalows/${id}`, undefined, true),
    reservations: (status?: string) => request<Reservation[]>('GET', '/api/admin/reservations' + qs({ status }), undefined, true),
    setReservationStatus: (id: number, status: ReservationStatus) =>
      request<Reservation>('PATCH', `/api/admin/reservations/${id}`, { status }, true),
    stats: () => request<AdminStats>('GET', '/api/admin/stats', undefined, true),
    ragStats: () => request<RagStats>('GET', '/api/admin/rag/stats', undefined, true),
    ragReindex: (force: boolean) => request<{ started: boolean }>('POST', '/api/admin/rag/reindex', { force }, true),
    ragSearch: (query: string, top_k?: number) => request<SearchTrace>('POST', '/api/admin/rag/search', { query, top_k }, true),
    voiceSessions: () => request<VoiceSessionListItem[]>('GET', '/api/admin/voice/sessions', undefined, true),
    voiceSession: (id: number) => request<VoiceSessionDetail>('GET', `/api/admin/voice/sessions/${id}`, undefined, true),
    chatTest: (message: string, session_id?: string) => request<AdminChatResponse>('POST', '/api/admin/chat/test', { session_id, message }, true),
  },
}
