import React, { useState } from 'react'
import { ThemedSwitch } from '@/components/ThemedSwitch'
import type { CompareMode, PortalFilters, PortalQuery } from '@/types/portalAnalytics'
import { COMPARE_OPTIONS, RANGE_PRESETS, CHANNEL_LABELS } from './format'

export interface FilterOptions {
  channel: string[]
  country: string[]
  device_type: string[]
}

const FILTER_FIELDS: { key: keyof PortalFilters; label: string }[] = [
  { key: 'channel', label: 'Canal' },
  { key: 'country', label: 'País' },
  { key: 'device_type', label: 'Dispositivo' },
]

const CUSTOM = 'custom'

const toLocalISODate = (d: Date): string =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

interface Props {
  query: PortalQuery
  options: FilterOptions
  onChange: (next: PortalQuery) => void
}

/** RF-063: rango con comparación, filtros combinables y los dos interruptores de limpieza activos por defecto. */
export const PortalControls: React.FC<Props> = ({ query, options, onChange }) => {
  const isCustom = 'since' in query.range
  const [draft, setDraft] = useState({
    since: 'since' in query.range ? query.range.since : '',
    until: 'until' in query.range ? query.range.until : '',
  })

  // Al pasar a "Personalizado" se parte del rango que ya se veía, con fechas válidas.
  const startCustom = () => {
    const until = new Date()
    const since = new Date(until)
    since.setDate(until.getDate() - ('days' in query.range ? query.range.days : 30) + 1)
    const next = { since: toLocalISODate(since), until: toLocalISODate(until) }
    setDraft(next)
    onChange({ ...query, range: next })
  }

  const setFilter = (key: keyof PortalFilters, value: string) => {
    const filters = { ...query.filters }
    if (value) filters[key] = value
    else delete filters[key]
    onChange({ ...query, filters })
  }

  const applyDraft = (next: { since: string; until: string }) => {
    setDraft(next)
    if (next.since && next.until && next.since <= next.until) onChange({ ...query, range: next })
  }

  const hasFilters = Object.keys(query.filters).length > 0

  return (
    <div className="card mb-6">
      <div className="card-body flex flex-wrap items-end gap-x-6 gap-y-4">
        <label className="flex flex-col gap-1 text-xs text-text-secondary">
          Rango
          <select
            className="input-field w-auto"
            aria-label="Rango de fechas"
            value={isCustom ? CUSTOM : String('days' in query.range ? query.range.days : 30)}
            onChange={(e) => (e.target.value === CUSTOM ? startCustom() : onChange({ ...query, range: { days: Number(e.target.value) } }))}
          >
            {RANGE_PRESETS.map((p) => (
              <option key={p.days} value={p.days}>
                {p.label}
              </option>
            ))}
            <option value={CUSTOM}>Personalizado…</option>
          </select>
        </label>

        {isCustom && (
          <div className="flex items-end gap-2">
            <label className="flex flex-col gap-1 text-xs text-text-secondary">
              Desde
              <input type="date" className="input-field" aria-label="Desde" value={draft.since} onChange={(e) => applyDraft({ ...draft, since: e.target.value })} />
            </label>
            <label className="flex flex-col gap-1 text-xs text-text-secondary">
              Hasta
              <input type="date" className="input-field" aria-label="Hasta" value={draft.until} onChange={(e) => applyDraft({ ...draft, until: e.target.value })} />
            </label>
          </div>
        )}

        <label className="flex flex-col gap-1 text-xs text-text-secondary">
          Comparar con
          <select
            className="input-field w-auto"
            aria-label="Comparar con"
            value={query.compare}
            onChange={(e) => onChange({ ...query, compare: e.target.value as CompareMode })}
          >
            {COMPARE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        {FILTER_FIELDS.map(({ key, label }) => (
          <label key={key} className="flex flex-col gap-1 text-xs text-text-secondary">
            {label}
            <select className="input-field w-auto" aria-label={`Filtrar por ${label.toLowerCase()}`} value={query.filters[key] ?? ''} onChange={(e) => setFilter(key, e.target.value)}>
              <option value="">Todos</option>
              {[...new Set([...(query.filters[key] ? [query.filters[key] as string] : []), ...options[key]])].map((v) => (
                <option key={v} value={v}>
                  {key === 'channel' ? (CHANNEL_LABELS[v] ?? v) : v}
                </option>
              ))}
            </select>
          </label>
        ))}

        {hasFilters && (
          <button type="button" className="btn-secondary text-sm" onClick={() => onChange({ ...query, filters: {} })}>
            Quitar filtros
          </button>
        )}

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 ml-auto">
          <label className="flex items-center gap-2 text-sm text-text">
            <ThemedSwitch aria-label="Excluir bots" checked={query.excludeBots} onChange={(v) => onChange({ ...query, excludeBots: v })} />
            Excluir bots
          </label>
          <label className="flex items-center gap-2 text-sm text-text">
            <ThemedSwitch aria-label="Excluir mis visitas" checked={query.excludeOwner} onChange={(v) => onChange({ ...query, excludeOwner: v })} />
            Excluir mis visitas
          </label>
        </div>
      </div>
    </div>
  )
}
