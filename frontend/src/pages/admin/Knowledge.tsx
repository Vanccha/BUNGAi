import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { AlertTriangle, Bot, CheckCircle2, Loader2, Minus, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { api } from '../../api/client'
import type { KnowledgeEntry, KnowledgeMode } from '../../api/types'
import { ConfirmModal, ErrorBox, Field, Modal, Spinner } from '../../components/ui'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../lib/useAsync'
import { errMsg } from '../../lib/format'
import { PageHead } from './AdminLayout'

const DEFAULT_CATS = ['Genel', 'Konaklama', 'Yeme-İçme', 'Aktiviteler', 'Politikalar', 'Ulaşım', 'SSS']
type Draft = Pick<KnowledgeEntry, 'category' | 'title' | 'content' | 'is_active' | 'sort_order' | 'mode'> & { id?: number }
const empty: Draft = { category: 'Genel', title: '', content: '', is_active: true, sort_order: 0, mode: 'always' }

/** Kaba token tahmini (Türkçe için ~3,5 karakter / token) */
const roughTokens = (t: string) => Math.ceil(t.length / 3.5)

const MODE_HELP: Record<KnowledgeMode, string> = {
  always: 'Her mesajda botun yönergesine eklenir; bot bunu hep bilir. Kısa ve kritik bilgiler için uygundur (kurallar, saatler, fiyat özeti). Toplam 20.000 token sınırı vardır.',
  search: 'Uzun belgeler (menü, ayrıntılı SSS, broşür) için. Bot yalnızca konuyla ilgili olduğunda arayıp ilgili bölümleri bulur. Sınır yoktur; indekslenmesi birkaç saniye sürer.',
}

function ModeToggle({ mode, onChange }: { mode: KnowledgeMode; onChange: (m: KnowledgeMode) => void }) {
  const opts: { v: KnowledgeMode; label: string }[] = [{ v: 'always', label: 'Her zaman bilinsin' }, { v: 'search', label: 'Gerektiğinde aransın' }]
  return (
    <div className="inline-flex rounded-full bg-navy-50 p-0.5 text-xs font-semibold" role="group">
      {opts.map(o => (
        <button key={o.v} type="button" title={MODE_HELP[o.v]} onClick={() => mode !== o.v && onChange(o.v)}
          className={`px-3 py-1.5 rounded-full transition ${mode === o.v ? (o.v === 'always' ? 'bg-navy-800 text-white' : 'bg-aegean-600 text-white') : 'text-navy-600 hover:bg-white'}`}>{o.label}</button>
      ))}
    </div>
  )
}

function IndexPill({ k }: { k: KnowledgeEntry }) {
  if (k.mode === 'always' || k.index_status === 'not_applicable')
    return <span className="inline-flex items-center gap-1 text-xs text-stone-400" title="Her zaman bilinen kayıtlar indekslenmez"><Minus size={12} />—</span>
  if (k.index_status === 'pending')
    return <span className="inline-flex items-center gap-1 text-xs rounded-full bg-amber-50 text-amber-800 px-2 py-0.5 font-semibold"><Loader2 size={12} className="animate-spin" />İndeksleniyor</span>
  if (k.index_status === 'error')
    return <span className="inline-flex items-center gap-1 text-xs rounded-full bg-red-50 text-red-700 px-2 py-0.5 font-semibold"><AlertTriangle size={12} />Hata</span>
  return <span className="inline-flex items-center gap-1 text-xs rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5 font-semibold"><CheckCircle2 size={12} />İndekslendi · {k.chunk_count} parça</span>
}

export default function KnowledgePage() {
  const toast = useToast()
  const { data, loading, error, reload, setData } = useAsync(() => api.admin.knowledge(), [])
  const [cat, setCat] = useState('')
  const [q, setQ] = useState('')
  const [edit, setEdit] = useState<Draft | null>(null)
  const [del, setDel] = useState<KnowledgeEntry | null>(null)
  const [busy, setBusy] = useState(false)

  const anyPending = (data ?? []).some(k => k.mode === 'search' && k.index_status === 'pending')
  useEffect(() => {
    if (!anyPending) return
    const t = setInterval(() => { api.admin.knowledge().then(setData).catch(() => { /* sessizce yoksay */ }) }, 2000)
    return () => clearInterval(t)
  }, [anyPending, setData])

  const cats = useMemo(() => Array.from(new Set([...DEFAULT_CATS, ...(data ?? []).map(k => k.category)])), [data])
  const grouped = useMemo(() => {
    const list = (data ?? []).filter(k => (!cat || k.category === cat) && (!q || (k.title + k.content).toLowerCase().includes(q.toLowerCase())))
      .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
    const m = new Map<string, KnowledgeEntry[]>()
    list.forEach(k => m.set(k.category, [...(m.get(k.category) ?? []), k]))
    return [...m.entries()]
  }, [data, cat, q])

  const save = async (e: FormEvent) => {
    e.preventDefault()
    if (!edit) return
    setBusy(true)
    const { id, ...body } = edit
    try {
      if (id) await api.admin.updateKnowledge(id, body); else await api.admin.createKnowledge(body)
      toast.ok(body.mode === 'search' ? 'Kaydedildi. Belge arka planda indeksleniyor.' : 'Bilgi kaydedildi. Bot artık güncel bilgiyi kullanacak.')
      setEdit(null); await reload()
    } catch (e2) { toast.err(errMsg(e2)) } finally { setBusy(false) }
  }
  const remove = async (k: KnowledgeEntry) => {
    setDel(null)
    try { await api.admin.deleteKnowledge(k.id); toast.ok('Silindi'); await reload() } catch (e) { toast.err(errMsg(e)) }
  }
  const patch = async (k: KnowledgeEntry, p: Partial<Draft>) => {
    try {
      await api.admin.updateKnowledge(k.id, { category: k.category, title: k.title, content: k.content, is_active: k.is_active, sort_order: k.sort_order, mode: k.mode, ...p })
      await reload()
    } catch (e) { toast.err(errMsg(e)) }
  }

  return (
    <>
      <PageHead title="Chatbot Bilgi Bankası" desc="Sohbet asistanı müşterilere yalnızca bu kayıtlardaki bilgilere dayanarak cevap verir. Kısa bilgiler her zaman bilinir; uzun belgeler (menü gibi) gerektiğinde aranır. Değişikliklerinizi 'Bot Test' sayfasından deneyebilirsiniz.">
        <button className="btn btn-primary" onClick={() => setEdit({ ...empty })}><Plus size={16} />Yeni Bilgi</button>
      </PageHead>

      <div className="card p-4 mb-6 flex gap-3 items-start bg-pool-50 border-pool-200">
        <Bot className="text-aegean-600 shrink-0 mt-0.5" size={20} />
        <p className="text-sm text-navy-800">İpucu: Fiyat, kural ve sık sorulan soruları açık ve kısa cümlelerle yazın. Pasif kayıtlar bota gönderilmez. Uzun belgeleri &quot;Gerektiğinde aransın&quot; moduna alın.</p>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
          <input className="input !pl-9" placeholder="Ara…" value={q} onChange={e => setQ(e.target.value)} />
        </div>
        <select className="input !w-auto" value={cat} onChange={e => setCat(e.target.value)}>
          <option value="">Tüm kategoriler</option>
          {cats.map(c => <option key={c}>{c}</option>)}
        </select>
      </div>

      {loading && !data ? <Spinner /> : error ? <ErrorBox text={error} /> : grouped.length === 0 ? <p className="text-stone-500">Kayıt bulunamadı.</p> : (
        <div className="space-y-8">
          {grouped.map(([c, items]) => (
            <section key={c}>
              <h2 className="text-2xl text-gold-700 mb-3">{c} <span className="text-xs text-stone-400 font-sans">({items.length})</span></h2>
              <div className="grid gap-3">
                {items.map(k => (
                  <div key={k.id} className={`card p-4 flex gap-4 items-start ${k.is_active ? '' : 'opacity-60'}`}>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-navy-900">{k.title}</span>
                        <span className={`text-[11px] rounded-full px-2 py-0.5 font-semibold ${k.mode === 'always' ? 'bg-navy-100 text-navy-800' : 'bg-pool-100 text-aegean-600'}`} title={MODE_HELP[k.mode]}>{k.mode === 'always' ? 'Her zaman bilinir' : 'Aranır'}</span>
                        <IndexPill k={k} />
                      </div>
                      <p className="text-sm text-stone-600 mt-1 line-clamp-3 whitespace-pre-line">{k.content}</p>
                      <div className="flex flex-wrap items-center gap-3 mt-2">
                        <span className="text-xs text-stone-400">Sıra: {k.sort_order} · ~{roughTokens(k.content).toLocaleString('tr-TR')} token</span>
                        <ModeToggle mode={k.mode} onChange={m => patch(k, { mode: m })} />
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <label className="flex items-center cursor-pointer mr-2" title={k.is_active ? 'Aktif' : 'Pasif'}>
                        <input type="checkbox" className="sr-only peer" checked={k.is_active} onChange={() => patch(k, { is_active: !k.is_active })} />
                        <span className="w-10 h-6 bg-stone-300 peer-checked:bg-gold-500 rounded-full relative transition after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-5 after:h-5 after:bg-white after:rounded-full after:transition peer-checked:after:translate-x-4" />
                      </label>
                      <button className="p-2 rounded-lg hover:bg-pool-100" onClick={() => setEdit({ ...k })} aria-label="Düzenle"><Pencil size={16} /></button>
                      <button className="p-2 rounded-lg hover:bg-red-50 text-red-600" onClick={() => setDel(k)} aria-label="Sil"><Trash2 size={16} /></button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {del && <ConfirmModal danger title="Bilgiyi sil" text={`"${del.title}" silinsin mi? Bu işlem geri alınamaz.`} confirmLabel="Sil" onConfirm={() => remove(del)} onClose={() => setDel(null)} />}

      {edit && (
        <Modal wide title={edit.id ? 'Bilgiyi Düzenle' : 'Yeni Bilgi'} onClose={() => setEdit(null)}>
          <form onSubmit={save} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Kategori">
                <input className="input" list="kcats" value={edit.category} onChange={e => setEdit({ ...edit, category: e.target.value })} required />
                <datalist id="kcats">{cats.map(c => <option key={c} value={c} />)}</datalist>
              </Field>
              <Field label="Sıra" hint="Küçük sayı önce gelir"><input type="number" className="input" value={edit.sort_order} onChange={e => setEdit({ ...edit, sort_order: Number(e.target.value) })} /></Field>
            </div>
            <Field label="Başlık"><input className="input" value={edit.title} onChange={e => setEdit({ ...edit, title: e.target.value })} required /></Field>
            <Field label="Bilgi modu" hint={MODE_HELP[edit.mode]}>
              <ModeToggle mode={edit.mode} onChange={m => setEdit({ ...edit, mode: m })} />
            </Field>
            <Field label="İçerik" hint="Botun müşteriye aktaracağı bilgi. Menü gibi uzun belgeleri buraya yapıştırabilirsiniz.">
              <textarea rows={18} className="input font-mono !text-[13px] leading-relaxed min-h-[320px] resize-y" value={edit.content} onChange={e => setEdit({ ...edit, content: e.target.value })} required />
              <div className="flex justify-between gap-3 text-xs text-stone-500 mt-1">
                <span>{edit.content.length.toLocaleString('tr-TR')} karakter</span>
                <span className={edit.mode === 'always' && roughTokens(edit.content) > 5000 ? 'text-amber-700 font-semibold' : ''}>
                  ≈ {roughTokens(edit.content).toLocaleString('tr-TR')} token (kaba tahmin){edit.mode === 'always' && roughTokens(edit.content) > 5000 ? ' — uzun belge, "Gerektiğinde aransın" önerilir' : ''}
                </span>
              </div>
            </Field>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={edit.is_active} onChange={e => setEdit({ ...edit, is_active: e.target.checked })} />Aktif (bot bu bilgiyi kullansın)</label>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="btn btn-ghost" onClick={() => setEdit(null)}>Vazgeç</button>
              <button className="btn btn-primary" disabled={busy}>Kaydet</button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
