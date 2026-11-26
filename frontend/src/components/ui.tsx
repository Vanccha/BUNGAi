import { useState, type ReactNode } from 'react'
import { ImageOff, Loader2, X } from 'lucide-react'
import type { ReservationStatus } from '../api/types'
import { statusColor, statusLabel } from '../lib/format'

export function SafeImage({ src, alt, className = '' }: { src?: string; alt: string; className?: string }) {
  const [failed, setFailed] = useState(false)
  if (!src || failed)
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-pool-200 via-pool-50 to-gold-100 text-navy-400 ${className}`} role="img" aria-label={alt}>
        <ImageOff size={32} strokeWidth={1.5} />
      </div>
    )
  return <img src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} className={`object-cover ${className}`} />
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-navy-600">
      <Loader2 className="animate-spin" size={22} />{label && <span className="text-sm">{label}</span>}
    </div>
  )
}

export function ErrorBox({ text }: { text: string }) {
  return <div className="rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3">{text}</div>
}

export function StatusBadge({ status }: { status: ReservationStatus }) {
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusColor[status]}`}>{statusLabel[status]}</span>
}

export function Modal({ title, onClose, children, wide }: { title: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-navy-900/50 p-0 sm:p-4" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className={`pop bg-white w-full ${wide ? 'sm:max-w-3xl' : 'sm:max-w-xl'} max-h-[92vh] overflow-y-auto rounded-t-3xl sm:rounded-3xl shadow-2xl`}>
        <div className="sticky top-0 bg-white flex items-center justify-between px-6 py-4 border-b border-pool-100 z-10">
          <h3 className="text-lg font-semibold text-navy-800">{title}</h3>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-pool-100" aria-label="Kapat"><X size={20} /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}

export function ConfirmModal({ title, text, confirmLabel, onConfirm, onClose, danger }: { title: string; text: string; confirmLabel: string; onConfirm: () => void; onClose: () => void; danger?: boolean }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="text-sm text-navy-800">{text}</p>
      <div className="flex justify-end gap-3 pt-5">
        <button className="btn btn-ghost" onClick={onClose}>Vazgeç</button>
        <button className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`} onClick={onConfirm}>{confirmLabel}</button>
      </div>
    </Modal>
  )
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {hint && <p className="text-xs text-stone-500 mt-1">{hint}</p>}
    </div>
  )
}

export function ListEditor({ items, onChange, placeholder, addLabel }: { items: string[]; onChange: (v: string[]) => void; placeholder: string; addLabel: string }) {
  return (
    <div className="space-y-2">
      {items.map((it, i) => (
        <div key={i} className="flex gap-2">
          <input className="input" value={it} placeholder={placeholder} onChange={e => onChange(items.map((x, j) => (j === i ? e.target.value : x)))} />
          <button type="button" className="btn btn-ghost !px-3" onClick={() => onChange(items.filter((_, j) => j !== i))} aria-label="Sil"><X size={16} /></button>
        </div>
      ))}
      <button type="button" className="btn btn-ghost !py-1.5 text-xs" onClick={() => onChange([...items, ''])}>+ {addLabel}</button>
    </div>
  )
}
