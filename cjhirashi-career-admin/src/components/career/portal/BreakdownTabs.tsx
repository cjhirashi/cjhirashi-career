import React, { useState } from 'react'
import { Globe2 } from 'lucide-react'
import { EmptyState, SectionCard } from '@/components/career/MetricsCharts'
import { WorldBubbleMap } from '@/components/career/WorldBubbleMap'
import { usePortalBreakdown, usePortalDevices, usePortalGeo, usePortalPages } from '@/hooks/usePortalAnalytics'
import type { PortalMetricsOverview } from '@/types/career'
import type { PortalQuery } from '@/types/portalAnalytics'
import { BreakdownTable } from './BreakdownTable'
import { formatDuration, formatNumber, formatRate, shortPath } from './format'

type TabKey = 'sources' | 'pages' | 'location' | 'devices'
const TABS: { key: TabKey; label: string }[] = [
  { key: 'sources', label: 'Fuentes' },
  { key: 'pages', label: 'Páginas' },
  { key: 'location', label: 'Ubicación' },
  { key: 'devices', label: 'Dispositivos' },
]

const SOURCE_DIMENSIONS = [
  { value: 'channel', label: 'Canales' },
  { value: 'source', label: 'Fuentes' },
  { value: 'utm_campaign', label: 'Campañas' },
  { value: 'referrer_domain', label: 'Sitios de referencia' },
]
const DEVICE_DIMENSIONS = [
  { value: 'device_type', label: 'Tipo de dispositivo' },
  { value: 'browser', label: 'Navegador' },
  { value: 'os', label: 'Sistema operativo' },
  { value: 'language', label: 'Idioma' },
] as const
const GEO_LEVELS = [
  { value: 'country', label: 'País' },
  { value: 'region', label: 'Región' },
  { value: 'city', label: 'Ciudad' },
] as const

const Segment = <T extends string>({ options, value, onChange, label }: { options: readonly { value: T; label: string }[]; value: T; onChange: (v: T) => void; label: string }) => (
  <select className="input-field w-auto mb-4" aria-label={label} value={value} onChange={(e) => onChange(e.target.value as T)}>
    {options.map((o) => (
      <option key={o.value} value={o.value}>
        {o.label}
      </option>
    ))}
  </select>
)

const Loading = () => <p className="text-text-secondary text-sm py-6 text-center">Cargando…</p>

const SourcesPanel: React.FC<{ query: PortalQuery }> = ({ query }) => {
  const [dimension, setDimension] = useState('channel')
  const { data, isLoading } = usePortalBreakdown(query, dimension)
  return (
    <>
      <Segment options={SOURCE_DIMENSIONS} value={dimension} onChange={setDimension} label="Agrupar fuentes por" />
      {isLoading ? <Loading /> : <BreakdownTable rows={data?.rows ?? []} keyLabel={SOURCE_DIMENSIONS.find((d) => d.value === dimension)?.label ?? ''} translateChannel={dimension === 'channel'} />}
    </>
  )
}

const PagesPanel: React.FC<{ query: PortalQuery }> = ({ query }) => {
  const { data, isLoading } = usePortalPages(query)
  if (isLoading) return <Loading />
  if (!data || data.rows.length === 0) return <EmptyState message="Sin vistas de página en este rango." />
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-text-secondary text-xs">
            <th className="py-2 pr-3 font-medium">Página</th>
            <th className="py-2 px-2 font-medium text-right">Vistas</th>
            <th className="py-2 px-2 font-medium text-right">Visitantes</th>
            <th className="py-2 px-2 font-medium text-right">Entradas</th>
            <th className="py-2 px-2 font-medium text-right">Salida</th>
            <th className="py-2 px-2 font-medium text-right">Mediana</th>
            <th className="py-2 pl-2 font-medium text-right">Scroll</th>
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row) => (
            <tr key={row.page} className="border-t border-border">
              <td className="py-2 pr-3 text-text min-w-[10rem] break-all" title={row.page}>{shortPath(row.page, 48)}</td>
              <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatNumber(row.pageviews)}</td>
              <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatNumber(row.visitors)}</td>
              <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatNumber(row.entries)}</td>
              <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatRate(row.exit_rate)}</td>
              <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatDuration(row.median_active_ms)}</td>
              <td className="py-2 pl-2 text-right mono whitespace-nowrap">{row.avg_max_scroll_pct === null ? '—' : `${row.avg_max_scroll_pct} %`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const LocationPanel: React.FC<{ query: PortalQuery; overview?: PortalMetricsOverview }> = ({ query, overview }) => {
  const [level, setLevel] = useState<'country' | 'region' | 'city'>('country')
  const { data, isLoading } = usePortalGeo(query, level)
  return (
    <>
      <Segment options={GEO_LEVELS} value={level} onChange={setLevel} label="Nivel de ubicación" />
      {isLoading ? <Loading /> : <BreakdownTable rows={data?.rows ?? []} keyLabel={GEO_LEVELS.find((l) => l.value === level)?.label ?? ''} />}
      {overview && (
        <div className="mt-6">
          <p className="text-text-secondary text-xs mb-2 flex items-center gap-1.5">
            <Globe2 size={14} aria-hidden="true" /> El tamaño de cada punto es proporcional a las visitas desde esa ciudad
          </p>
          <WorldBubbleMap data={overview.visits_by_location} />
        </div>
      )}
    </>
  )
}

const DevicesPanel: React.FC<{ query: PortalQuery }> = ({ query }) => {
  const [by, setBy] = useState<'device_type' | 'browser' | 'os' | 'language'>('device_type')
  const { data, isLoading } = usePortalDevices(query, by)
  return (
    <>
      <Segment options={DEVICE_DIMENSIONS} value={by} onChange={setBy} label="Agrupar dispositivos por" />
      {isLoading ? <Loading /> : <BreakdownTable rows={data?.rows ?? []} keyLabel={DEVICE_DIMENSIONS.find((d) => d.value === by)?.label ?? ''} />}
    </>
  )
}

interface Props {
  query: PortalQuery
  overview?: PortalMetricsOverview
}

/** RF-062: una pestaña activa a la vez; solo la visible pide sus datos. */
export const BreakdownTabs: React.FC<Props> = ({ query, overview }) => {
  const [tab, setTab] = useState<TabKey>('sources')
  return (
    <SectionCard title="Desglose" subtitle="De dónde llegan, qué ven, desde dónde y con qué" icon={Globe2}>
      <div role="tablist" aria-label="Desglose" className="flex flex-wrap gap-2 mb-4">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={tab === t.key ? 'btn-primary text-sm' : 'btn-secondary text-sm'}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" aria-label={TABS.find((t) => t.key === tab)?.label}>
        {tab === 'sources' && <SourcesPanel query={query} />}
        {tab === 'pages' && <PagesPanel query={query} />}
        {tab === 'location' && <LocationPanel query={query} overview={overview} />}
        {tab === 'devices' && <DevicesPanel query={query} />}
      </div>
    </SectionCard>
  )
}
