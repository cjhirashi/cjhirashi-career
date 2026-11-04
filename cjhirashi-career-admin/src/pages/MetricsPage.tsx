import React, { useState } from 'react'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'
import { PortalControls, type FilterOptions } from '@/components/career/portal/PortalControls'
import { KpiRow } from '@/components/career/portal/KpiRow'
import { TrendChart } from '@/components/career/portal/TrendChart'
import { BreakdownTabs } from '@/components/career/portal/BreakdownTabs'
import { GoalsFunnel } from '@/components/career/portal/GoalsFunnel'
import { PathsRetention } from '@/components/career/portal/PathsRetention'
import { DataQuality } from '@/components/career/portal/DataQuality'
import { rangeLabel } from '@/components/career/portal/format'
import { usePortalBreakdown, usePortalKpis, usePortalOverview, usePortalTrend } from '@/hooks/usePortalAnalytics'
import type { PortalQuery } from '@/types/portalAnalytics'

/** RF-063: los dos interruptores de limpieza arrancan activos. */
const DEFAULT_QUERY: PortalQuery = {
  range: { days: 30 },
  compare: 'none',
  excludeBots: true,
  excludeOwner: true,
  filters: {},
}

/** Valores para los filtros: se piden sin filtros para que elegir uno no vacíe las demás listas. */
const useFilterOptions = (query: PortalQuery): FilterOptions => {
  const open: PortalQuery = { ...query, filters: {}, compare: 'none' }
  const channel = usePortalBreakdown(open, 'channel')
  const country = usePortalBreakdown(open, 'country')
  const device = usePortalBreakdown(open, 'device_type')
  const keys = (rows?: { key: string | null }[]) => (rows ?? []).map((r) => r.key).filter((k): k is string => !!k)
  return { channel: keys(channel.data?.rows), country: keys(country.data?.rows), device_type: keys(device.data?.rows) }
}

export const MetricsPage: React.FC = () => {
  const [query, setQuery] = useState<PortalQuery>(DEFAULT_QUERY)
  const kpis = usePortalKpis(query)
  const trend = usePortalTrend(query)
  const overview = usePortalOverview(query)
  const withBots = usePortalKpis({ ...query, excludeBots: false, compare: 'none' })
  const options = useFilterOptions(query)

  const comparing = query.compare !== 'none'
  const error = kpis.error ?? trend.error

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-text">Métricas del Portafolio</h1>
        <p className="text-text-secondary mt-2">
          Cómo se usa cjhirashi.com: quién llega, de dónde, qué ve y qué hace. {rangeLabel(query.range)}
          {comparing ? ', con comparación' : ''}.
        </p>
      </div>

      <PortalControls query={query} options={options} onChange={setQuery} />

      {(kpis.isLoading || trend.isLoading) && <LoadingSpinner fullScreen={false} message="Cargando métricas..." />}
      {error && <p className="text-red-600 dark:text-red-400 text-sm" role="alert">{getErrorMessage(error)}</p>}

      {kpis.data && trend.data && (
        <div className="space-y-6">
          <KpiRow kpis={kpis.data} points={trend.data.points} />
          <TrendChart trend={trend.data} comparing={comparing} />
          <BreakdownTabs query={query} overview={overview.data} />
          <GoalsFunnel query={query} />
          <PathsRetention query={query} />
          <DataQuality
            query={query}
            visits={kpis.data.sample_size.visits}
            visitors={kpis.data.sample_size.visitors}
            visitsWithBots={withBots.data?.sample_size.visits ?? null}
          />
        </div>
      )}
    </div>
  )
}
