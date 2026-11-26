import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Loader2, Lock } from 'lucide-react'
import { api } from '../../api/client'
import { ErrorBox, Field } from '../../components/ui'
import { errMsg } from '../../lib/format'
import { useAuth } from './AdminLayout'

export default function LoginPage() {
  const { token, login } = useAuth()
  const nav = useNavigate()
  const [u, setU] = useState('')
  const [p, setP] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  if (token) return <Navigate to="/admin" replace />

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr(null)
    try {
      const r = await api.admin.login(u, p)
      login(r.access_token)
      nav('/admin', { replace: true })
    } catch (e2) { setErr(errMsg(e2)); setBusy(false) }
  }
  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-900 via-navy-700 to-aegean-600 flex items-center justify-center p-5">
      <form onSubmit={submit} className="bg-white rounded-3xl p-8 w-full max-w-sm shadow-2xl space-y-4 fade-up">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-navy-100 text-navy-700 flex items-center justify-center mb-3"><Lock size={22} /></div>
          <h1 className="text-2xl text-navy-800">Yönetici Girişi</h1>
        </div>
        <Field label="Kullanıcı adı"><input className="input" value={u} onChange={e => setU(e.target.value)} autoComplete="username" required autoFocus /></Field>
        <Field label="Şifre"><input type="password" className="input" value={p} onChange={e => setP(e.target.value)} autoComplete="current-password" required /></Field>
        {err && <ErrorBox text={err} />}
        <button disabled={busy} className="btn btn-primary w-full !py-3">{busy && <Loader2 size={16} className="animate-spin" />}Giriş Yap</button>
      </form>
    </div>
  )
}
