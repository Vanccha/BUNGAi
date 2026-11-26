import { useEffect, useState, type FormEvent } from 'react'
import { AlertTriangle, ChevronDown, ChevronRight, Info, Loader2, RefreshCw, Search } from 'lucide-react'
import { api } from '../../api/client'
import type { SearchTrace } from '../../api/types'
import { ConfirmModal, ErrorBox, Spinner } from '../../components/ui'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../lib/useAsync'
import { errMsg, fmtDateTime } from '../../lib/format'
import { PageHead } from './AdminLayout'

const f = (n: number | null | undefined, d = 3) => (n == null ? '—' : n.toFixed(d))

export default function RagPage() {
  const toast = useToast()
  const { data: st, loading, error, reload, setData } = useAsync(() => api.admin.ragStats(), [])
  const [confirmAll, setConfirmAll] = useState(false)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')
  const [searching, setSearching] = useState(false)
  const [trace, setTrace] = useState<SearchTrace | null>(null)
  const [searchErr, setSearchErr] = useState<string | null>(null)
  const [open, setOpen] = useState<Set<number>>(new Set())

  const pending = (st?.pending_entries ?? 0) > 0
  useEffect(() => {
    if (!pending) return
    const t = setInterval(() => { api.admin.ragStats().then(setData).catch(() => { /* yoksay */ }) }, 2000)
    return () => clearInterval(t)
  }, [pending, setData])

  const reindex = async (force: boolean) => {
    setConfirmAll(false); setBusy(true)
    try { await api.admin.ragReindex(force); toast.ok('İndeksleme başlatıldı'); await reload() } catch (e) { toast.err(errMsg(e)) } finally { setBusy(false) }
  }
  const search = async (e: FormEvent) => {
    e.preventDefault()
    if (!q.trim()) return
    setSearching(true); setSearchErr(null); setOpen(new Set())
    try { setTrace(await api.admin.ragSearch(q.trim(), 8)) } catch (e2) { setSearchErr(errMsg(e2)); setTrace(null) } finally { setSearching(false) }
  }
  const pct = st ? Math.min(100, (st.always_tokens / Math.max(1, st.always_token_limit)) * 100) : 0
  const warn = pct > 75
  const counts: [string, number][] = st ? [['Aranan kayıt', st.search_entries], ['Parça', st.chunks], ['İndekslendi', st.indexed_entries], ['Bekliyor', st.pending_entries], ['Hata', st.error_entries]] : []

  return (
    <>
      <PageHead title="RAG & Arama" desc="Uzun belgelerin (menü, ayrıntılı SSS) bot tarafından nasıl bulunduğunu izleyin ve aramayı deneyin.">
        <div className="flex flex-wrap gap-2">
          <button className="btn btn-primary" disabled={busy} onClick={() => reindex(false)}><RefreshCw size={16} className={busy ? 'animate-spin' : ''} />Değişenleri indeksle</button>
          <button className="btn btn-ghost" disabled={busy} onClick={() => setConfirmAll(true)}>Tümünü yeniden indeksle</button>
        </div>
      </PageHead>

      {loading && !st ? <Spinner /> : error ? <ErrorBox text={error} /> : st && (
        <div className="space-y-6">
          {!st.embeddings_enabled && (
            <div className="flex gap-3 items-start rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 px-4 py-3 text-sm">
              <AlertTriangle size={18} className="shrink-0 mt-0.5" />
              <span><b>API anahtarı yok, sadece kelime araması çalışıyor.</b> Vektör (anlam) araması için embedding API anahtarını sunucuya ekleyin.</span>
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <div className="card p-5">
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="text-2xl text-navy-900">Her zaman bilinen bilgi</h2>
                <span className={`text-sm font-bold ${warn ? 'text-amber-700' : 'text-navy-800'}`}>{st.always_tokens.toLocaleString('tr-TR')} / {st.always_token_limit.toLocaleString('tr-TR')} token</span>
              </div>
              <div className="mt-3 h-3.5 rounded-full bg-navy-50 overflow-hidden" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
                <div className={`h-full rounded-full transition-all ${warn ? 'bg-gradient-to-r from-amber-400 to-red-500' : 'bg-gradient-to-r from-aegean-500 to-gold-400'}`} style={{ width: `${pct}%` }} />
              </div>
              <p className="text-xs text-stone-500 mt-2">{st.always_entries} kayıt · %{pct.toFixed(0)} dolu{warn && <span className="text-amber-700 font-semibold"> — sınıra yaklaşıyor; uzun belgeleri &quot;Gerektiğinde aransın&quot; moduna alın.</span>}</p>
            </div>
            <div className="card p-5 grid grid-cols-3 gap-3 text-center">
              {counts.map(([l, v]) => (
                <div key={l}>
                  <div className={`text-3xl font-display font-bold ${l === 'Hata' && v > 0 ? 'text-red-600' : 'text-navy-900'}`}>{v}</div>
                  <div className="text-xs text-stone-500">{l}{l === 'Bekliyor' && pending && <Loader2 size={11} className="inline ml-1 animate-spin" />}</div>
                </div>
              ))}
              <div className="col-span-3 border-t border-navy-100 pt-3 text-xs text-stone-600 text-left space-y-0.5">
                <div>Embedding modeli: <span className="font-mono text-navy-800">{st.embedding_model || '—'}</span></div>
                <div>Son indeksleme: {st.last_indexed_at ? fmtDateTime(st.last_indexed_at) : '—'}</div>
              </div>
            </div>
          </div>

          <div className="card p-5 bg-pool-50 border-pool-200 text-sm text-navy-800 space-y-2">
            <div className="flex items-center gap-2 font-semibold text-navy-900"><Info size={16} />Arama nasıl çalışıyor?</div>
            <p><b>Vektör araması</b> sorunun anlamına yakın bölümleri bulur (örn. &ldquo;vejetaryen&rdquo; &rarr; sebze yemekleri). <b>Kelime araması</b> aynı sözcüklerin geçtiği bölümleri bulur (örn. oda adı, fiyat). İki sıralama <b>RRF</b> (Reciprocal Rank Fusion) ile tek listede birleştirilir. Sonuçlar <b>güven eşiğini</b> geçemezse bot &ldquo;bu konuda bilgim yok&rdquo; der, bilgi uydurmaz.</p>
            <p className="text-xs text-navy-700">Ayrıntılı rehber için depodaki <code className="bg-white px-1 rounded">RAG_REHBERI.md</code> dosyasına bakın.</p>
          </div>

          <div className="card p-5">
            <h2 className="text-2xl text-navy-900 mb-3">Arama Testi</h2>
            <form onSubmit={search} className="flex gap-2">
              <div className="relative flex-1">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
                <input className="input !pl-9" value={q} onChange={e => setQ(e.target.value)} placeholder="Örn: vejetaryen yemek var mı?" />
              </div>
              <button className="btn btn-primary" disabled={searching || !q.trim()}>{searching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}Ara</button>
            </form>
            {searchErr && <div className="mt-3"><ErrorBox text={searchErr} /></div>}
            {trace && (
              <div className="mt-4 space-y-3">
                <div className="text-xs text-stone-500">Normalize edilmiş sorgu: <span className="font-mono text-navy-800">{trace.normalized_query}</span></div>
                {trace.below_threshold && (
                  <div className="flex gap-2 items-start rounded-xl bg-amber-50 border border-amber-300 text-amber-900 px-3 py-2 text-sm font-semibold">
                    <AlertTriangle size={16} className="mt-0.5 shrink-0" />Hiçbir sonuç güven eşiğini geçemedi — bot bu soruya bilgi bulamamış sayılır.
                  </div>
                )}
                {trace.results.length === 0 ? <p className="text-sm text-stone-500">Sonuç yok.</p> : (
                  <div className="overflow-x-auto rounded-xl border border-navy-100">
                    <table className="w-full text-sm">
                      <thead className="bg-navy-50 text-navy-700 text-xs text-left">
                        <tr><th className="p-2.5">Kayıt</th><th className="p-2.5">Parça</th><th className="p-2.5">Vektör (sıra)</th><th className="p-2.5">Kelime (sıra)</th><th className="p-2.5">Birleşik</th></tr>
                      </thead>
                      <tbody>
                        {trace.results.map((h, i) => (
                          <tr key={i} className="border-t border-navy-100 align-top">
                            <td className="p-2.5 min-w-[160px]"><div className="font-semibold text-navy-900">{h.entry_title}</div><div className="text-xs text-stone-500">{h.category} · parça #{h.chunk_index}</div></td>
                            <td className="p-2.5 min-w-[260px] max-w-md">
                              <button onClick={() => setOpen(o => { const n = new Set(o); if (n.has(i)) n.delete(i); else n.add(i); return n })} className="flex gap-1 text-left text-stone-700">
                                {open.has(i) ? <ChevronDown size={14} className="mt-0.5 shrink-0" /> : <ChevronRight size={14} className="mt-0.5 shrink-0" />}
                                <span className={`whitespace-pre-line ${open.has(i) ? '' : 'line-clamp-2'}`}>{h.text}</span>
                              </button>
                            </td>
                            <td className="p-2.5 font-mono text-xs whitespace-nowrap">{f(h.vector_score)} <span className="text-stone-400">({h.vector_rank ?? '—'})</span></td>
                            <td className="p-2.5 font-mono text-xs whitespace-nowrap">{f(h.keyword_score, 2)} <span className="text-stone-400">({h.keyword_rank ?? '—'})</span></td>
                            <td className="p-2.5 font-mono text-xs font-bold text-gold-700">{f(h.fused_score, 4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {confirmAll && <ConfirmModal title="Tümünü yeniden indeksle" text="Tüm 'Gerektiğinde aransın' kayıtları baştan indekslenecek. Bu işlem embedding API kullanır ve kayıt sayısına göre birkaç dakika sürebilir. Devam edilsin mi?" confirmLabel="Evet, yeniden indeksle" onConfirm={() => reindex(true)} onClose={() => setConfirmAll(false)} />}
    </>
  )
}
