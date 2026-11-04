import React from 'react'
import { Line, LineChart, ResponsiveContainer } from 'recharts'
import { Radio } from 'lucide-react'
import { usePortalRealtime } from '@/hooks/usePortalAnalytics'
import { CHART_COLORS } from '@/components/career/MetricsCharts'
import type { PortalKpis, PortalKpisResponse, PortalTrendPoint } from '@/types/portalAnalytics'
import { deltaTone, formatDeltaPct, formatDuration, formatNumber, formatRate } from './format'

interface TileSpec {
  metric: keyof PortalKpis
  label: string
  format: (kpis: PortalKpis) => string
  /** Campo de la serie diaria para la minigráfica; los cocientes no tienen. */
  spark?: keyof Pick<PortalTrendPoint, 'visitors' | 'visits' | 'pageviews'>
}

const TILES: TileSpec[] = [
  { metric: 'visitors', label: 'Visitantes', format: (k) => formatNumber(k.visitors), spark: 'visitors' },
  { metric: 'visits', label: 'Visitas', format: (k) => formatNumber(k.visits), spark: 'visits' },
  { metric: 'pageviews', label: 'Vistas de página', format: (k) => formatNumber(k.pageviews), spark: 'pageviews' },
  { metric: 'pages_per_visit', label: 'Páginas por visita', format: (k) => formatNumber(k.pages_per_visit, 2) },
  { metric: 'bounce_rate', label: 'Tasa de rebote', format: (k) => formatRate(k.bounce_rate) },
  { metric: 'median_active_ms', label: 'Duración mediana', format: (k) => formatDuration(k.median_active_ms) },
]

const TONE_CLASS = { good: 'text-green-600 dark:text-green-400', bad: 'text-red-600 dark:text-red-400', neutral: 'text-text-secondary' }

interface Props {
  kpis: PortalKpisResponse
  points: PortalTrendPoint[]
}

export const KpiRow: React.FC<Props> = ({ kpis, points }) => {
  const { data: realtime } = usePortalRealtime()
  const comparing = kpis.compare && kpis.compare !== 'none'

  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(9.5rem,1fr))] gap-4 mb-6">
      {TILES.map((tile) => {
        const delta = kpis.deltas?.[tile.metric]
        return (
          <div key={tile.metric} className="stat-card" data-testid={`kpi-${tile.metric}`}>
            <p className="text-text-secondary text-xs font-medium">{tile.label}</p>
            <p className="text-2xl font-bold text-text mono mt-1 whitespace-nowrap">{tile.format(kpis.kpis)}</p>
            {comparing && (
              <p className={`text-xs mt-1 font-medium whitespace-nowrap ${TONE_CLASS[deltaTone(tile.metric, delta)]}`} aria-label={`Cambio de ${tile.label}`}>
                {formatDeltaPct(delta)}
              </p>
            )}
            {tile.spark && points.length > 1 && (
              <div className="h-8 mt-2" aria-hidden="true">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={points}>
                    <Line type="monotone" dataKey={tile.spark} stroke={CHART_COLORS[0]} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )
      })}
      <div className="stat-card" data-testid="kpi-now">
        <p className="text-text-secondary text-xs font-medium flex items-center gap-1.5">
          <Radio size={13} className="text-primary" aria-hidden="true" />
          Visitantes ahora
        </p>
        <p className="text-2xl font-bold text-text mono mt-1 whitespace-nowrap">{realtime ? formatNumber(realtime.visitors_now) : '—'}</p>
        <p className="text-text-secondary text-xs mt-1">{realtime ? `Últimos ${realtime.window_minutes} min` : 'Cargando…'}</p>
      </div>
    </div>
  )
}
