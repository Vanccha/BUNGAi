import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'

type T = { id: number; kind: 'ok' | 'err'; text: string }
const Ctx = createContext<{ ok: (t: string) => void; err: (t: string) => void }>({ ok() {}, err() {} })
export const useToast = () => useContext(Ctx)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [list, setList] = useState<T[]>([])
  const push = useCallback((kind: T['kind'], text: string) => {
    const id = Date.now() + Math.random()
    setList(l => [...l, { id, kind, text }])
    setTimeout(() => setList(l => l.filter(x => x.id !== id)), 4000)
  }, [])
  return (
    <Ctx.Provider value={{ ok: t => push('ok', t), err: t => push('err', t) }}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-[calc(100%-2rem)] max-w-sm">
        {list.map(t => (
          <div key={t.id} className={`pop flex items-start gap-2 rounded-xl px-4 py-3 text-sm shadow-lg text-white ${t.kind === 'ok' ? 'bg-navy-700' : 'bg-red-700'}`}>
            {t.kind === 'ok' ? <CheckCircle2 size={18} className="mt-0.5 shrink-0" /> : <XCircle size={18} className="mt-0.5 shrink-0" />}
            <span>{t.text}</span>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  )
}
