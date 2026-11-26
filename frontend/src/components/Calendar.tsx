import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../api/client'
import { iso, parseISO, today } from '../lib/format'

const monthKey = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
const DAYS = ['Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct', 'Pz']

export function Calendar({ bungalowId, checkIn, checkOut, onChange }: {
  bungalowId: number
  checkIn: string
  checkOut: string
  onChange: (ci: string, co: string) => void
}) {
  const [view, setView] = useState(() => { const d = checkIn ? parseISO(checkIn) : new Date(); return new Date(d.getFullYear(), d.getMonth(), 1) })
  const [booked, setBooked] = useState<Set<string>>(new Set())
  const [err, setErr] = useState(false)

  useEffect(() => {
    let alive = true
    const next = new Date(view.getFullYear(), view.getMonth() + 1, 1)
    Promise.all([api.calendar(bungalowId, monthKey(view)), api.calendar(bungalowId, monthKey(next))])
      .then(([a, b]) => { if (alive) { setBooked(prev => new Set([...prev, ...a.booked_dates, ...b.booked_dates])); setErr(false) } })
      .catch(() => { if (alive) setErr(true) })
    return () => { alive = false }
  }, [bungalowId, view])

  const t = today()
  const pick = (day: string) => {
    if (!checkIn || (checkIn && checkOut) || day <= checkIn) onChange(day, '')
    else onChange(checkIn, day)
  }

  const renderMonth = (base: Date) => {
    const first = new Date(base.getFullYear(), base.getMonth(), 1)
    const offset = (first.getDay() + 6) % 7
    const count = new Date(base.getFullYear(), base.getMonth() + 1, 0).getDate()
    const cells: (string | null)[] = Array(offset).fill(null)
    for (let d = 1; d <= count; d++) cells.push(iso(new Date(base.getFullYear(), base.getMonth(), d)))
    return (
      <div className="flex-1 min-w-[250px]">
        <div className="text-center font-semibold text-navy-800 mb-2 capitalize">
          {base.toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' })}
        </div>
        <div className="grid grid-cols-7 text-center text-[11px] text-stone-500 mb-1">{DAYS.map(d => <div key={d}>{d}</div>)}</div>
        <div className="grid grid-cols-7 gap-y-1">
          {cells.map((c, i) => {
            if (!c) return <div key={i} />
            const isBooked = booked.has(c)
            const past = c < t
            const disabled = isBooked || past
            const start = c === checkIn
            const end = c === checkOut
            const inRange = checkIn && checkOut && c > checkIn && c < checkOut
            return (
              <button
                key={i}
                type="button"
                disabled={disabled}
                onClick={() => pick(c)}
                title={isBooked ? 'Dolu' : undefined}
                className={`h-9 text-sm transition rounded-lg
                  ${disabled ? 'text-stone-300 cursor-not-allowed' : 'hover:bg-pool-100 text-navy-900'}
                  ${isBooked ? 'line-through bg-stone-100' : ''}
                  ${inRange ? 'bg-pool-100 rounded-none' : ''}
                  ${start || end ? '!bg-gold-500 !text-white' : ''}`}
              >
                {Number(c.slice(8))}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  const next = new Date(view.getFullYear(), view.getMonth() + 1, 1)
  const prevDisabled = monthKey(view) <= monthKey(new Date())
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <button type="button" disabled={prevDisabled} onClick={() => setView(new Date(view.getFullYear(), view.getMonth() - 1, 1))} className="p-1.5 rounded-full hover:bg-pool-100 disabled:opacity-30" aria-label="Önceki ay"><ChevronLeft size={20} /></button>
        <span className="text-xs text-stone-500">{!checkIn ? 'Giriş tarihini seçin' : !checkOut ? 'Çıkış tarihini seçin' : 'Tarihler seçildi'}</span>
        <button type="button" onClick={() => setView(next)} className="p-1.5 rounded-full hover:bg-pool-100" aria-label="Sonraki ay"><ChevronRight size={20} /></button>
      </div>
      <div className="flex flex-wrap gap-x-8 gap-y-6">
        {renderMonth(view)}
        <div className="hidden md:block flex-1 min-w-[250px]">{renderMonth(next)}</div>
      </div>
      <div className="flex gap-4 mt-3 text-xs text-stone-500">
        <span className="flex items-center gap-1"><i className="w-3 h-3 rounded bg-gold-500" />Seçili</span>
        <span className="flex items-center gap-1"><i className="w-3 h-3 rounded bg-stone-200" />Dolu</span>
        {err && <span className="text-red-600">Takvim yüklenemedi</span>}
      </div>
    </div>
  )
}
