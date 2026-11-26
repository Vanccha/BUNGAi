import { useState, type FormEvent } from 'react'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { api } from '../../api/client'
import type { Bungalow } from '../../api/types'
import { ErrorBox, Field, ListEditor, Modal, SafeImage, Spinner } from '../../components/ui'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../lib/useAsync'
import { errMsg, tl } from '../../lib/format'
import { PageHead } from './AdminLayout'

type Draft = Omit<Bungalow, 'id'> & { id?: number }
const empty: Draft = { slug: '', name: '', short_description: '', description: '', capacity: 2, bedrooms: 1, size_m2: 40, price_per_night: 3000, amenities: [], images: [], is_active: true }
const slugify = (s: string) => s.toLowerCase().replace(/ı/g, 'i').replace(/ğ/g, 'g').replace(/ü/g, 'u').replace(/ş/g, 's').replace(/ö/g, 'o').replace(/ç/g, 'c').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

export default function AdminBungalowsPage() {
  const toast = useToast()
  const { data, loading, error, reload } = useAsync(() => api.admin.bungalows(), [])
  const [edit, setEdit] = useState<Draft | null>(null)
  const [busy, setBusy] = useState(false)

  const save = async (e: FormEvent) => {
    e.preventDefault(); if (!edit) return
    setBusy(true)
    const { id, ...rest } = edit
    const body = { ...rest, amenities: rest.amenities.map(a => a.trim()).filter(Boolean), images: rest.images.map(a => a.trim()).filter(Boolean), slug: rest.slug || slugify(rest.name) }
    try {
      if (id) await api.admin.updateBungalow(id, body); else await api.admin.createBungalow(body)
      toast.ok('Kayıt kaydedildi'); setEdit(null); await reload()
    } catch (e2) { toast.err(errMsg(e2)) } finally { setBusy(false) }
  }
  const remove = async (b: Bungalow) => {
    if (!confirm(`"${b.name}" silinsin mi?`)) return
    try { await api.admin.deleteBungalow(b.id); toast.ok('Silindi'); await reload() } catch (e) { toast.err(errMsg(e)) }
  }
  const num = (k: 'capacity' | 'bedrooms' | 'size_m2' | 'price_per_night') => (e: { target: { value: string } }) => setEdit(d => d && { ...d, [k]: Number(e.target.value) })

  return (
    <>
      <PageHead title="Villalar & Bungalovlar" desc="Siteye görünecek villa ve bungalovları yönetin. Pasif kayıtlar sitede listelenmez.">
        <button className="btn btn-primary" onClick={() => setEdit({ ...empty })}><Plus size={16} />Yeni Villa</button>
      </PageHead>
      {loading ? <Spinner /> : error ? <ErrorBox text={error} /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-stone-500 border-b border-pool-100"><tr><th className="p-3">Bungalov</th><th className="p-3">Kapasite</th><th className="p-3">Fiyat / gece</th><th className="p-3">Durum</th><th className="p-3" /></tr></thead>
            <tbody>
              {data?.map(b => (
                <tr key={b.id} className="border-b border-pool-50 last:border-0">
                  <td className="p-3"><div className="flex items-center gap-3"><SafeImage src={b.images[0]} alt={b.name} className="w-14 h-10 rounded-lg" /><div><div className="font-semibold text-navy-800">{b.name}</div><div className="text-xs text-stone-400">/{b.slug}</div></div></div></td>
                  <td className="p-3">{b.capacity} kişi · {b.bedrooms} oda</td>
                  <td className="p-3 whitespace-nowrap">{tl(b.price_per_night)}</td>
                  <td className="p-3"><span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${b.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-stone-200 text-stone-600'}`}>{b.is_active ? 'Aktif' : 'Pasif'}</span></td>
                  <td className="p-3 text-right whitespace-nowrap">
                    <button className="p-2 rounded-lg hover:bg-pool-100" onClick={() => setEdit({ ...b })} aria-label="Düzenle"><Pencil size={16} /></button>
                    <button className="p-2 rounded-lg hover:bg-red-50 text-red-600" onClick={() => remove(b)} aria-label="Sil"><Trash2 size={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {edit && (
        <Modal wide title={edit.id ? 'Bungalovu Düzenle' : 'Yeni Villa / Bungalov'} onClose={() => setEdit(null)}>
          <form onSubmit={save} className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label="Ad"><input className="input" value={edit.name} onChange={e => setEdit({ ...edit, name: e.target.value, slug: edit.id ? edit.slug : slugify(e.target.value) })} required /></Field>
              <Field label="Slug (URL)"><input className="input" value={edit.slug} onChange={e => setEdit({ ...edit, slug: e.target.value })} required /></Field>
            </div>
            <Field label="Kısa açıklama"><input className="input" value={edit.short_description} onChange={e => setEdit({ ...edit, short_description: e.target.value })} /></Field>
            <Field label="Açıklama"><textarea rows={4} className="input" value={edit.description} onChange={e => setEdit({ ...edit, description: e.target.value })} /></Field>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <Field label="Kapasite"><input type="number" min={1} className="input" value={edit.capacity} onChange={num('capacity')} /></Field>
              <Field label="Yatak odası"><input type="number" min={0} className="input" value={edit.bedrooms} onChange={num('bedrooms')} /></Field>
              <Field label="m²"><input type="number" min={1} className="input" value={edit.size_m2} onChange={num('size_m2')} /></Field>
              <Field label="Gecelik fiyat (TL)"><input type="number" min={0} step="0.01" className="input" value={edit.price_per_night} onChange={num('price_per_night')} /></Field>
            </div>
            <Field label="Olanaklar"><ListEditor items={edit.amenities} onChange={amenities => setEdit({ ...edit, amenities })} placeholder="örn. Jakuzi" addLabel="Olanak ekle" /></Field>
            <Field label="Görseller (URL)"><ListEditor items={edit.images} onChange={images => setEdit({ ...edit, images })} placeholder="https://…" addLabel="Görsel ekle" /></Field>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={edit.is_active} onChange={e => setEdit({ ...edit, is_active: e.target.checked })} />Aktif (sitede göster)</label>
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
