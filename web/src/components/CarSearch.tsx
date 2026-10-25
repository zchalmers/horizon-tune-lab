import { useState, useCallback } from 'react'
import { searchCars, type CarResult } from '../api/client'

interface Props {
  onSelectCar?: (car: CarResult) => void
}

function classBadge(car: CarResult) {
  if (!car.class_letter && !car.pi) return '—'
  return `${car.class_letter ?? ''}${car.pi ?? ''}`
}

export default function CarSearch({ onSelectCar }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<CarResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const doSearch = useCallback(async () => {
    const q = query.trim()
    if (!q) return
    setLoading(true)
    setSearched(true)
    try {
      const res = await searchCars(q)
      setResults(res.results)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [query])

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') doSearch()
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
        <label className="space-y-2">
          <span className="lab-label">Search by make or model</span>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ferrari, Supra, Lambo…"
            maxLength={80}
            className="lab-input"
          />
        </label>
        <button
          onClick={doSearch}
          disabled={loading || !query.trim()}
          className="lab-button-primary self-end"
        >
          {loading ? 'Searching…' : 'Search index'}
        </button>
      </div>

      {searched && results.length === 0 && !loading && (
        <div className="border border-stone-300 bg-stone-50 p-4 text-sm text-stone-600">
          No cars found. Try a make, model, or shorter search term.
        </div>
      )}

      {results.length > 0 && (
        <div className="border border-stone-300 bg-white">
          <div className="grid grid-cols-[minmax(0,1fr)_90px] border-b border-stone-300 bg-stone-100/70 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500">
            <span>Car</span>
            <span className="text-right">Class</span>
          </div>
          {results.map(car => (
            <button
              key={car.id}
              onClick={() => onSelectCar?.(car)}
              className="grid w-full grid-cols-[minmax(0,1fr)_90px] items-center gap-3 border-b border-stone-200 px-3 py-3 text-left transition last:border-b-0 hover:bg-stone-50"
            >
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-neutral-950">{car.full_name}</span>
                <span className="mt-1 block truncate text-xs text-stone-500">
                  {[car.year, car.car_type].filter(Boolean).join(' · ') || 'FH6 index entry'}
                </span>
              </span>
              <span className="lab-mono justify-self-end border border-stone-300 bg-stone-100 px-2 py-1 text-xs font-semibold text-neutral-800">
                {classBadge(car)}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
