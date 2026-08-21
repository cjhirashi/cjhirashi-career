import React from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { Target, TrendingUp, Handshake, Building2, Scale, ClipboardList } from 'lucide-react'
import { useSearchOverview } from '@/hooks/useCareerResource'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'
import { BedrockCostPanel } from '@/components/bedrock/BedrockCostPanel'

/** Fixed palette reusing the app's theme tokens (adapts light/dark
 * automatically, same as badges elsewhere) plus a few neutral fallbacks for
 * breakdowns with more categories than semantic colors (e.g. 5 role
 * categories, 6+ track categories). */
const CHART_COLORS = [
  'var(--primary-color)',
  'var(--success-text)',
  'var(--warning-text)',
  'var(--error-text)',
  '#8b5cf6',
  '#ec4899',
  '#64748b',
  '#0ea5e9',
]

const axisTickStyle = { fill: 'var(--text-secondary)', fontSize: 12 }

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <p className="text-text-secondary text-sm text-center py-10">{message}</p>
)

interface Breakdown {
  label: string
  count: number
}

const BreakdownPie: React.FC<{ data: Breakdown[]; emptyMessage: string }> = ({ data, emptyMessage }) => {
  if (data.length === 0) return <EmptyState message={emptyMessage} />
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="label" cx="50%" cy="50%" outerRadius={80} label>
          {data.map((entry, i) => (
            <Cell key={entry.label} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-secondary)' }} />
        <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8 }} />
      </PieChart>
    </ResponsiveContainer>
  )
}

const BreakdownBar: React.FC<{ data: Breakdown[]; emptyMessage: string }> = ({ data, emptyMessage }) => {
  if (data.length === 0) return <EmptyState message={emptyMessage} />
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ left: 12, right: 12 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
        <XAxis type="number" allowDecimals={false} tick={axisTickStyle} />
        <YAxis type="category" dataKey="label" width={110} tick={axisTickStyle} />
        <Tooltip
          contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8 }}
          cursor={{ fill: 'var(--primary-light)' }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {data.map((entry, i) => (
            <Cell key={entry.label} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

const SectionCard: React.FC<{ title: string; subtitle?: string; icon: React.ElementType; children: React.ReactNode }> = ({
  title,
  subtitle,
  icon: Icon,
  children,
}) => (
  <div className="card">
    <div className="card-header">
      <h2 className="text-base font-semibold text-text flex items-center gap-2">
        <Icon size={17} className="text-primary" aria-hidden="true" />
        {title}
      </h2>
      {subtitle && <p className="text-text-secondary text-xs mt-1">{subtitle}</p>}
    </div>
    <div className="card-body">{children}</div>
  </div>
)

export const SearchMetricsPage: React.FC = () => {
  const { data, isLoading, isError, error } = useSearchOverview()

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Métricas de Búsqueda</h1>
        <p className="text-text-secondary mt-2">
          Visualización de la estrategia de Operativa de Búsqueda: embudo de conversión, triage de vacantes,
          segmentación de mercado, networking y avance del plan activo.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando métricas..." />}

      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

      {!isLoading && !isError && data && (
        <div className="space-y-6">
          {/* Embudo de conversión */}
          <SectionCard
            title="Embudo de Conversión"
            subtitle="De vacante encontrada a oferta - vacancies → applications → interviews → ofertas"
            icon={TrendingUp}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {data.funnel.map((stage, i) => (
                <div key={stage.label} className="stat-card">
                  <p className="text-text-secondary text-sm font-medium">{stage.label}</p>
                  <p
                    className="text-3xl font-bold mono mt-2"
                    style={{ color: CHART_COLORS[i % CHART_COLORS.length] }}
                  >
                    {stage.value}
                  </p>
                </div>
              ))}
            </div>
          </SectionCard>

          {/* Vacantes: triage */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <SectionCard title="Fit de Vacantes" subtitle="Calculado con el rubro de Factores de Fit" icon={Target}>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <p className="text-text-secondary text-xs">Promedio</p>
                  <p className="text-2xl font-bold text-text mono mt-1">{data.fit_percentage_avg ?? '—'}</p>
                </div>
                <div>
                  <p className="text-text-secondary text-xs">Mínimo</p>
                  <p className="text-2xl font-bold text-text mono mt-1">{data.fit_percentage_min ?? '—'}</p>
                </div>
                <div>
                  <p className="text-text-secondary text-xs">Máximo</p>
                  <p className="text-2xl font-bold text-text mono mt-1">{data.fit_percentage_max ?? '—'}</p>
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Vacantes por Evaluación" icon={Target}>
              <BreakdownPie data={data.vacancies_by_evaluation} emptyMessage="Aún no hay vacantes registradas." />
            </SectionCard>

            <SectionCard title="Vacantes por Track" icon={Target}>
              <BreakdownBar data={data.vacancies_by_track} emptyMessage="Aún no hay vacantes registradas." />
            </SectionCard>
          </div>

          {/* Segmentos de mercado */}
          <SectionCard
            title="Segmentos de Mercado"
            subtitle="Aplicaciones, respuestas y entrevistas logradas por canal activo"
            icon={Scale}
          >
            {data.market_segments.length === 0 ? (
              <EmptyState message="Aún no hay segmentos de mercado registrados." />
            ) : (
              <ResponsiveContainer width="100%" height={Math.max(220, data.market_segments.length * 50)}>
                <BarChart data={data.market_segments} layout="vertical" margin={{ left: 12, right: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={axisTickStyle} />
                  <YAxis
                    type="category"
                    dataKey="channel_name"
                    width={140}
                    tick={axisTickStyle}
                  />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8 }}
                    cursor={{ fill: 'var(--primary-light)' }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-secondary)' }} />
                  <Bar dataKey="applications_made" name="Aplicaciones" fill={CHART_COLORS[0]} radius={[0, 4, 4, 0]} />
                  <Bar dataKey="responses_received" name="Respuestas" fill={CHART_COLORS[1]} radius={[0, 4, 4, 0]} />
                  <Bar dataKey="interviews_achieved" name="Entrevistas" fill={CHART_COLORS[2]} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </SectionCard>

          {/* Networking */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SectionCard title="Contactos por Estado" icon={Handshake}>
              <BreakdownPie data={data.networking_by_status} emptyMessage="Aún no hay contactos registrados." />
            </SectionCard>
            <SectionCard title="Contactos por Categoría" icon={Handshake}>
              <BreakdownBar data={data.networking_by_category} emptyMessage="Aún no hay contactos registrados." />
            </SectionCard>
          </div>

          {/* Empresas diana */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SectionCard title="Empresas Diana por Tier" icon={Building2}>
              <BreakdownBar data={data.companies_by_tier} emptyMessage="Aún no hay empresas diana registradas." />
            </SectionCard>
            <SectionCard title="Empresas Diana por Estado" icon={Building2}>
              <BreakdownPie data={data.companies_by_status} emptyMessage="Aún no hay empresas diana registradas." />
            </SectionCard>
          </div>

          {/* Rubro de fit + plan activo */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SectionCard title="Rubro de Factores de Fit" subtitle="Peso de cada factor en el cálculo" icon={Scale}>
              {data.fit_scoring_factors.length === 0 ? (
                <EmptyState message="Aún no hay factores de fit registrados." />
              ) : (
                <BreakdownPie
                  data={data.fit_scoring_factors.map((f) => ({ label: f.factor_name, count: f.weight_percentage ?? 0 }))}
                  emptyMessage="Aún no hay factores de fit registrados."
                />
              )}
            </SectionCard>

            <SectionCard title="Plan de Búsqueda Activo" icon={ClipboardList}>
              {!data.active_search_plan ? (
                <EmptyState message="No hay ningún plan de búsqueda en progreso." />
              ) : (
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-text-secondary">Avance</span>
                      <span className="text-text font-semibold mono">
                        {data.active_search_plan.completion_percentage}%
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-glass overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${data.active_search_plan.completion_percentage}%`,
                          background: 'var(--primary-color)',
                        }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div>
                      <p className="text-text-secondary text-xs">CVs objetivo</p>
                      <p className="text-xl font-bold text-text mono mt-1">
                        {data.active_search_plan.target_cvs_sent}
                      </p>
                    </div>
                    <div>
                      <p className="text-text-secondary text-xs">Entrevistas objetivo</p>
                      <p className="text-xl font-bold text-text mono mt-1">
                        {data.active_search_plan.target_interviews}
                      </p>
                    </div>
                    <div>
                      <p className="text-text-secondary text-xs">Ofertas objetivo</p>
                      <p className="text-xl font-bold text-text mono mt-1">{data.active_search_plan.target_offers}</p>
                    </div>
                  </div>
                </div>
              )}
            </SectionCard>
          </div>

          {/* Agent Bedrock - independent of the search-overview data above */}
          <BedrockCostPanel />
        </div>
      )}
    </div>
  )
}
