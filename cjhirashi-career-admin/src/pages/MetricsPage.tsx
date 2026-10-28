import React, { useState } from 'react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { Eye, Globe2, FileText, TrendingUp, Timer } from 'lucide-react'
import { usePortalMetricsOverview } from '@/hooks/useCareerResource'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'
import { CHART_COLORS, axisTickStyle, EmptyState, BreakdownPie, BreakdownBar, SectionCard } from '@/components/career/MetricsCharts'
import { WorldBubbleMap } from '@/components/career/WorldBubbleMap'

/** `1250` -> "1m 15s"; `800` -> "800ms" below 1s, kept precise since most
 * real page visits land there. */
const formatDuration = (ms: number | null): string => {
  if (ms === null) return '—'
  if (ms < 1000) return `${ms}ms`
  const totalSeconds = Math.round(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`
}

const WINDOW_OPTIONS = [
  { value: 7, label: 'Últimos 7 días' },
  { value: 30, label: 'Últimos 30 días' },
  { value: 90, label: 'Últimos 90 días' },
]

export const MetricsPage: React.FC = () => {
  const [days, setDays] = useState(30)
  const { data, isLoading, isError, error } = usePortalMetricsOverview(days)

  const topCountry = data?.visits_by_country[0]?.label ?? '—'
  const topPage = data?.top_pages[0]?.label ?? '—'

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text">Métricas del Portafolio</h1>
          <p className="text-text-secondary mt-2">
            Tráfico del portafolio público: visitas en el tiempo, de qué países vienen y qué páginas se visitan más.
            Capturado en vivo por el propio portafolio (POST /events/track) en cada visita.
          </p>
        </div>
        <select
          className="input-field w-auto"
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          aria-label="Ventana de tiempo"
        >
          {WINDOW_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando métricas..." />}

      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

      {!isLoading && !isError && data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="stat-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm font-medium">Visitas totales</p>
                  <p className="text-3xl font-bold text-text mono mt-2">{data.total_visits}</p>
                </div>
                <Eye size={28} className="text-primary" aria-hidden="true" />
              </div>
              <p className="text-text-secondary text-xs mt-4">
                {data.total_pageviews} páginas vistas en total — varias páginas vistas en una misma sesión de
                navegación cuentan como 1 visita.
              </p>
            </div>

            <div className="stat-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm font-medium">
                    Visitas ({WINDOW_OPTIONS.find((o) => o.value === days)?.label.toLowerCase()})
                  </p>
                  <p className="text-3xl font-bold text-text mono mt-2">{data.visits_in_window}</p>
                </div>
                <TrendingUp size={28} className="text-primary" aria-hidden="true" />
              </div>
              <p className="text-text-secondary text-xs mt-4">{data.pageviews_in_window} páginas vistas en la ventana</p>
            </div>

            <div className="stat-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm font-medium">País principal</p>
                  <p className="text-xl font-bold text-text mt-2">{topCountry}</p>
                </div>
                <Globe2 size={28} className="text-primary" aria-hidden="true" />
              </div>
            </div>

            <div className="stat-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary text-sm font-medium">Página más visitada</p>
                  <p className="text-sm font-bold text-text mt-2 break-all">{topPage}</p>
                </div>
                <FileText size={28} className="text-primary" aria-hidden="true" />
              </div>
            </div>
          </div>

          <SectionCard
            title="Visitas en el tiempo"
            subtitle="Vistas de página por día en la ventana seleccionada"
            icon={TrendingUp}
          >
            {data.visits_by_day.length === 0 ? (
              <EmptyState message="Aún no hay visitas registradas en esta ventana." />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={data.visits_by_day} margin={{ left: 0, right: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="day" tick={axisTickStyle} />
                  <YAxis allowDecimals={false} tick={axisTickStyle} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    name="Visitas"
                    stroke={CHART_COLORS[0]}
                    fill={CHART_COLORS[0]}
                    fillOpacity={0.2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </SectionCard>

          <SectionCard
            title="Mapa de Visitas"
            subtitle="Mapa de burbujas - el tamaño de cada punto es proporcional al número de visitas desde esa ciudad"
            icon={Globe2}
          >
            <WorldBubbleMap data={data.visits_by_location} />
          </SectionCard>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SectionCard title="Visitas por País" subtitle="Resuelto por IP al momento de la visita" icon={Globe2}>
              <BreakdownPie data={data.visits_by_country} emptyMessage="Aún no hay visitas registradas." />
            </SectionCard>

            <SectionCard title="Páginas más visitadas" icon={FileText}>
              <BreakdownBar data={data.top_pages} emptyMessage="Aún no hay visitas registradas." />
            </SectionCard>
          </div>

          <SectionCard
            title="Tiempo en Página"
            subtitle="Cuánto se quedan realmente, no solo si entraron - capturado al cambiar de página o cerrar la pestaña"
            icon={Timer}
          >
            {data.duration_sample_size === 0 ? (
              <EmptyState message="Aún no hay mediciones de tiempo en página en esta ventana." />
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="stat-card">
                    <p className="text-text-secondary text-sm font-medium">Mínimo</p>
                    <p className="text-3xl font-bold text-text mono mt-2">{formatDuration(data.duration_ms_min)}</p>
                  </div>
                  <div className="stat-card">
                    <p className="text-text-secondary text-sm font-medium">Promedio</p>
                    <p className="text-3xl font-bold text-text mono mt-2">{formatDuration(data.duration_ms_avg)}</p>
                  </div>
                  <div className="stat-card">
                    <p className="text-text-secondary text-sm font-medium">Máximo</p>
                    <p className="text-3xl font-bold text-text mono mt-2">{formatDuration(data.duration_ms_max)}</p>
                  </div>
                </div>
                <p className="text-text-secondary text-xs mt-4">
                  {data.duration_sample_size} páginas vistas con tiempo medido en esta ventana.
                </p>
              </>
            )}
          </SectionCard>
        </div>
      )}
    </div>
  )
}
