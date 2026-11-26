import type { ReservationStatus } from '../api/types'

export const tl = (n: number) =>
  new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 2 }).format(n)

export const iso = (d: Date) => {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}
export const parseISO = (s: string) => {
  const [y, m, d] = s.split('-').map(Number)
  return new Date(y, m - 1, d)
}
export const addDays = (s: string, n: number) => { const d = parseISO(s); d.setDate(d.getDate() + n); return iso(d) }
export const today = () => iso(new Date())

export const fmtDate = (s: string) =>
  parseISO(s.slice(0, 10)).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })
export const fmtDateTime = (s: string) =>
  new Date(s).toLocaleString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

export const statusLabel: Record<ReservationStatus, string> = {
  pending_payment: 'Ödeme Bekliyor',
  confirmed: 'Onaylandı',
  cancelled: 'İptal Edildi',
  payment_failed: 'Ödeme Başarısız',
}
export const statusColor: Record<ReservationStatus, string> = {
  pending_payment: 'bg-amber-100 text-amber-800',
  confirmed: 'bg-emerald-100 text-emerald-800',
  cancelled: 'bg-stone-200 text-stone-700',
  payment_failed: 'bg-red-100 text-red-800',
}

export const errMsg = (e: unknown) => (e instanceof Error ? e.message : 'Beklenmeyen bir hata oluştu')

/** Yerel depolama yardımcıları (try/catch'li) */
export const store = {
  get(k: string): string | null { try { return localStorage.getItem(k) } catch { return null } },
  set(k: string, v: string) { try { localStorage.setItem(k, v) } catch { /* yoksay */ } },
  del(k: string) { try { localStorage.removeItem(k) } catch { /* yoksay */ } },
}
