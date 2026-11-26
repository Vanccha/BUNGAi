import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bot, User, Wrench } from 'lucide-react'
import { api } from '../../api/client'
import type { VoiceSessionListItem } from '../../api/types'
import { ErrorBox, Modal, Spinner } from '../../components/ui'
import { useAsync } from '../../lib/useAsync'
import { fmtDateTime } from '../../lib/format'
import { PageHead } from './AdminLayout'

const STATUS: Record<VoiceSessionListItem['status'], string> = {
  created: 'Başlamadı', active: 'Devam ediyor', ended: 'Tamamlandı', error: 'Hata',
}
const dur = (s: number) => `${Math.floor(s / 60)} dk ${String(s % 60).padStart(2, '0')} sn`

function Detail({ id, onClose }: { id: number; onClose: () => void }) {
  const { data, loading, error } = useAsync(() => api.admin.voiceSession(id), [id])
  return (
    <Modal title="Görüşme dökümü" onClose={onClose} wide>
      {loading ? <Spinner /> : error || !data ? <ErrorBox text={error ?? 'Alınamadı'} /> : (
        <div className="space-y-3">
          <div className="text-xs text-stone-500 flex flex-wrap gap-x-4 gap-y-1">
            <span>{fmtDateTime(data.started_at)}</span><span>{dur(data.duration_seconds)}</span>
            <span>{data.model} · {data.voice}</span>
            {data.reservation_codes.map(c => <Link key={c} to={`/rezervasyon/${c}`} className="font-mono underline text-navy-700">{c}</Link>)}
          </div>
          <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
            {data.transcript.length === 0 && <p className="text-sm text-stone-500">Döküm yok.</p>}
            {data.transcript.map((t, i) => t.role === 'tool' ? (
              <details key={i} className="rounded-xl border border-gold-200 bg-gold-50/60 px-3 py-2 text-xs">
                <summary className="cursor-pointer flex items-center gap-1.5 font-semibold text-gold-700"><Wrench size={12} />{t.name}{t.ms != null && <span className="font-normal text-stone-500"> · {t.ms} ms</span>}</summary>
                <pre className="mt-2 whitespace-pre-wrap break-words font-mono text-[11px] text-slate-700">{t.arguments}{'\n→ '}{t.output}</pre>
              </details>
            ) : (
              <div key={i} className={`flex gap-2 ${t.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-7 h-7 shrink-0 rounded-full flex items-center justify-center ${t.role === 'user' ? 'bg-navy-800 text-white' : 'bg-gold-100 text-gold-700'}`}>
                  {t.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${t.role === 'user' ? 'bg-navy-50' : 'bg-white border border-navy-100'}`}>
                  {t.text || <span className="text-stone-400">(anlaşılamadı)</span>}
                  {t.typed && <span className="ml-1 text-[10px] text-stone-400">(yazıldı)</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Modal>
  )
}

export default function VoiceSessionsPage() {
  const { data, loading, error } = useAsync(() => api.admin.voiceSessions(), [])
  const [sel, setSel] = useState<number | null>(null)
  return (
    <>
      <PageHead title="Sesli Görüşmeler" desc="Sesli asistanla yapılan görüşmelerin dökümü: arayanların ne sorduğunu buradan inceleyebilirsiniz." />
      {loading ? <Spinner /> : error ? <ErrorBox text={error} /> : (
        <div className="card overflow-x-auto">
          {data?.length === 0 ? <p className="p-6 text-sm text-stone-500">Henüz sesli görüşme yok.</p> : (
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-stone-500 border-b border-pool-100">
                <tr><th className="p-3">Tarih</th><th className="p-3">Süre</th><th className="p-3">Tur</th><th className="p-3">İlk soru</th><th className="p-3">Rezervasyon</th><th className="p-3">Durum</th></tr>
              </thead>
              <tbody>
                {data?.map(v => (
                  <tr key={v.id} onClick={() => setSel(v.id)} className="border-b border-pool-50 last:border-0 cursor-pointer hover:bg-gold-50/40">
                    <td className="p-3 whitespace-nowrap">{fmtDateTime(v.started_at)}</td>
                    <td className="p-3 whitespace-nowrap">{dur(v.duration_seconds)}</td>
                    <td className="p-3">{v.turn_count}</td>
                    <td className="p-3 max-w-[22rem] truncate">{v.first_user_text || <span className="text-stone-400">—</span>}</td>
                    <td className="p-3 font-mono text-xs">{v.reservation_codes.join(', ') || '—'}</td>
                    <td className="p-3">{STATUS[v.status]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
      {sel != null && <Detail id={sel} onClose={() => setSel(null)} />}
    </>
  )
}
