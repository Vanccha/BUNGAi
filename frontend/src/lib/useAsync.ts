import { useCallback, useEffect, useState, type DependencyList } from 'react'
import { errMsg } from './format'

export function useAsync<T>(fn: () => Promise<T>, deps: DependencyList) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fn, deps)
  const reload = useCallback(() => {
    setLoading(true)
    return run().then(d => { setData(d); setError(null) }).catch(e => setError(errMsg(e))).finally(() => setLoading(false))
  }, [run])
  useEffect(() => {
    let alive = true
    setLoading(true)
    run().then(d => { if (alive) { setData(d); setError(null) } })
      .catch(e => { if (alive) setError(errMsg(e)) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [run])
  return { data, loading, error, reload, setData }
}
