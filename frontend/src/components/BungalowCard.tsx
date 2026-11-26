import { Link } from 'react-router-dom'
import { BedDouble, Maximize2, Users } from 'lucide-react'
import type { Bungalow } from '../api/types'
import { tl } from '../lib/format'
import { SafeImage } from './ui'

export function BungalowCard({ b, query = '' }: { b: Bungalow; query?: string }) {
  return (
    <Link to={`/bungalovlar/${b.slug}${query}`} className="card group overflow-hidden flex flex-col hover:-translate-y-1 hover:shadow-xl transition duration-300">
      <div className="relative h-56 overflow-hidden">
        <SafeImage src={b.images[0]} alt={b.name} className="w-full h-full group-hover:scale-110 transition duration-[1200ms]" />
        <div className="absolute bottom-3 right-3 bg-white/95 rounded-full px-3.5 py-1 text-sm font-bold text-navy-900 shadow ring-1 ring-gold-300">
          {tl(b.price_per_night)} <span className="font-normal text-xs text-stone-500">/ gece</span>
        </div>
      </div>
      <div className="p-5 flex-1 flex flex-col">
        <h3 className="text-2xl font-semibold text-navy-900">{b.name}</h3>
        <p className="text-sm text-stone-600 mt-1.5 line-clamp-2 flex-1">{b.short_description}</p>
        <div className="flex gap-4 mt-4 text-xs text-aegean-600">
          <span className="flex items-center gap-1"><Users size={14} />{b.capacity} kişi</span>
          <span className="flex items-center gap-1"><BedDouble size={14} />{b.bedrooms} yatak odası</span>
          <span className="flex items-center gap-1"><Maximize2 size={14} />{b.size_m2} m²</span>
        </div>
      </div>
    </Link>
  )
}
