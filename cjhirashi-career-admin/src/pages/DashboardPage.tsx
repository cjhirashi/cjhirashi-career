import React from 'react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { Target, Briefcase, ClipboardList, Handshake, TrendingUp, Flag, Radar } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useWeeklyMetrics, useSearchOverview, useCareerCount } from '@/hooks/useCareerResource'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'
import {
  CHART_COLORS,
  axisTickStyle,
  BreakdownPie,
  BreakdownBar,
  SectionCard,
  KpiCard,
  TargetProgress,
  EmptyState,
} from '@/components/career/MetricsCharts'
import { KpiMetric } from '@/types/career'

const formatWeekStart = (value: string | null): string => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' })
}

const KpiRow: React.FC<{ kpis: KpiMetric[] }> = ({ kpis }) => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
    {kpis.map((kpi) => (
      <KpiCard key={kpi.label} label={kpi.label} valuePercentage={kpi.value_percentage} detail={kpi.detail} />
    ))}
  </div>
)

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  const { data: weeklyMetrics, isLoading: metricsLoading, isError: metricsError, error: metricsErrorObj } =
    useWeeklyMetrics(8)
  const { data: overview, isLoading: overviewLoading, isError: overviewError, error: overviewErrorObj } =
    useSearchOverview()
  const { data: vacanciesCount } = useCareerCount('vacancies')
  const { data: applicationsCount } = useCareerCount('applications')
  const { data: interviewsCount } = useCareerCount('interviews')
  const { data: contactsCount } = useCareerCount('networking-contacts')

  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Dashboard</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">Welcome back, {user?.full_name}!</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Vacantes</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">{vacanciesCount ?? '—'}</p>
            </div>
            <Target size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Vacantes en seguimiento</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Aplicaciones</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">{applicationsCount ?? '—'}</p>
            </div>
            <Briefcase size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Postulaciones enviadas</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Entrevistas</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">{interviewsCount ?? '—'}</p>
            </div>
            <ClipboardList size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Rondas realizadas</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Contactos</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">{contactsCount ?? '—'}</p>
            </div>
            <Handshake size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Red de networking</p>
        </div>
      </div>

      {/* Weekly Search Activity (GET /career/metrics/weekly) */}
      <div className="card mb-8">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Actividad de Búsqueda Semanal
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
            Aplicaciones, respuestas y entrevistas por semana
          </p>
        </div>
        <div className="card-body">
          {metricsLoading && <LoadingSpinner fullScreen={false} message="Cargando métricas..." />}

          {metricsError && (
            <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(metricsErrorObj)}</p>
          )}

          {!metricsLoading && !metricsError && (!Array.isArray(weeklyMetrics) || weeklyMetrics.length === 0) && (
            <p className="text-slate-600 dark:text-slate-400 text-sm text-center py-6">
              Aún no hay actividad de búsqueda registrada.
            </p>
          )}

          {!metricsLoading && !metricsError && Array.isArray(weeklyMetrics) && weeklyMetrics.length > 0 && (
            <div className="overflow-x-auto -mx-6">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 text-left text-slate-500 dark:text-slate-400">
                    <th className="px-6 py-2 font-medium whitespace-nowrap">Semana</th>
                    <th className="px-6 py-2 font-medium whitespace-nowrap">Aplicaciones</th>
                    <th className="px-6 py-2 font-medium whitespace-nowrap">Respuestas</th>
                    <th className="px-6 py-2 font-medium whitespace-nowrap">% Respuesta</th>
                    <th className="px-6 py-2 font-medium whitespace-nowrap">Entrevistas</th>
                    <th className="px-6 py-2 font-medium whitespace-nowrap">Ofertas</th>
                    <th className="px-6 py-2 font-medium whitespace-nowrap">Rechazos</th>
                  </tr>
                </thead>
                <tbody>
                  {weeklyMetrics.map((week, idx) => (
                    <tr
                      key={week.week_start ?? idx}
                      className="border-b border-slate-100 dark:border-slate-800 last:border-0"
                    >
                      <td className="px-6 py-2 whitespace-nowrap text-slate-900 dark:text-slate-100 mono">
                        {formatWeekStart(week.week_start)}
                      </td>
                      <td className="px-6 py-2 whitespace-nowrap mono">{week.applications_sent}</td>
                      <td className="px-6 py-2 whitespace-nowrap mono">{week.responses_received}</td>
                      <td className="px-6 py-2 whitespace-nowrap mono">
                        {week.response_rate_percentage !== null ? `${week.response_rate_percentage}%` : '—'}
                      </td>
                      <td className="px-6 py-2 whitespace-nowrap mono">{week.interviews_scheduled}</td>
                      <td className="px-6 py-2 whitespace-nowrap mono">{week.offers}</td>
                      <td className="px-6 py-2 whitespace-nowrap mono">{week.rejections}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Operativa de Búsqueda + Networking (GET /career/metrics/search-overview) */}
      {overviewLoading && <LoadingSpinner fullScreen={false} message="Cargando operativa de búsqueda..." />}

      {overviewError && (
        <p className="text-red-600 dark:text-red-400 text-sm mb-8">{getErrorMessage(overviewErrorObj)}</p>
      )}

      {!overviewLoading && !overviewError && overview && (
        <div className="space-y-6 mb-8">
          <SectionCard
            title="Embudo de Conversión"
            subtitle="Vacantes → aplicaciones → entrevistas → ofertas, con la tasa de conversión entre cada etapa"
            icon={TrendingUp}
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {overview.funnel.map((stage, i) => (
                <div key={stage.label} className="stat-card">
                  <p className="text-text-secondary text-sm font-medium">{stage.label}</p>
                  <p className="text-3xl font-bold mono mt-2" style={{ color: CHART_COLORS[i % CHART_COLORS.length] }}>
                    {stage.value}
                  </p>
                </div>
              ))}
            </div>
            <KpiRow kpis={overview.funnel_conversion_rates} />
          </SectionCard>

          <SectionCard
            title="Objetivos del Plan de Búsqueda"
            subtitle="Avance real contra las metas del plan activo - no solo actividad, sino si se está cumpliendo"
            icon={Flag}
          >
            {!overview.active_search_plan ? (
              <EmptyState message="No hay un plan de búsqueda activo con metas definidas." />
            ) : (
              <div className="space-y-4">
                <TargetProgress
                  label="Avance del plan"
                  actual={overview.active_search_plan.completion_percentage}
                  target={100}
                />
                <TargetProgress
                  label="CVs enviados"
                  actual={overview.funnel[1]?.value ?? 0}
                  target={overview.active_search_plan.target_cvs_sent}
                />
                <TargetProgress
                  label="Entrevistas"
                  actual={overview.funnel[2]?.value ?? 0}
                  target={overview.active_search_plan.target_interviews}
                />
                <TargetProgress
                  label="Ofertas"
                  actual={overview.funnel[3]?.value ?? 0}
                  target={overview.active_search_plan.target_offers}
                />
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Vacantes"
            subtitle="Calidad del triage: cuántas valen la pena aplicar, y cuántas de esas sí se aplicaron"
            icon={Target}
          >
            <div className="mb-6">
              <KpiRow
                kpis={[
                  ...overview.vacancy_kpis,
                  { label: 'Fit Promedio', value_percentage: overview.fit_percentage_avg, detail: null },
                ]}
              />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <p className="text-text-secondary text-xs font-medium mb-2">Vacantes por Evaluación</p>
                <BreakdownPie data={overview.vacancies_by_evaluation} emptyMessage="Aún no hay vacantes registradas." />
              </div>
              <div>
                <p className="text-text-secondary text-xs font-medium mb-2">Vacantes por Track</p>
                <BreakdownBar data={overview.vacancies_by_track} emptyMessage="Aún no hay vacantes registradas." />
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Vacantes por Plataforma"
            subtitle="De dónde vienen las vacantes y qué tan bien convierte cada canal - no solo volumen, sino resultado"
            icon={Radar}
          >
            {overview.vacancies_by_platform.length === 0 ? (
              <EmptyState message="Aún no hay vacantes con plataforma u origen registrado." />
            ) : (
              <ResponsiveContainer
                width="100%"
                height={Math.max(220, overview.vacancies_by_platform.length * 50)}
              >
                <BarChart data={overview.vacancies_by_platform} layout="vertical" margin={{ left: 12, right: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={axisTickStyle} />
                  <YAxis type="category" dataKey="platform" width={160} tick={axisTickStyle} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8 }}
                    cursor={{ fill: 'var(--primary-light)' }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-secondary)' }} />
                  <Bar dataKey="vacancies" name="Vacantes" fill={CHART_COLORS[0]} radius={[0, 4, 4, 0]} />
                  <Bar dataKey="applications" name="Aplicaciones" fill={CHART_COLORS[1]} radius={[0, 4, 4, 0]} />
                  <Bar dataKey="interviews" name="Entrevistas" fill={CHART_COLORS[2]} radius={[0, 4, 4, 0]} />
                  <Bar dataKey="offers" name="Ofertas" fill={CHART_COLORS[3]} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </SectionCard>

          <SectionCard title="Aplicaciones y Entrevistas" icon={Briefcase}>
            <div className="mb-6">
              <KpiRow
                kpis={[
                  {
                    label: 'Tasa de Respuesta en Aplicaciones',
                    value_percentage: overview.application_interactions_response_rate.rate_percentage,
                    detail: `${overview.application_interactions_response_rate.positive} de ${overview.application_interactions_response_rate.total}`,
                  },
                ]}
              />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <p className="text-text-secondary text-xs font-medium mb-2">Aplicaciones por Estado</p>
                <BreakdownPie
                  data={overview.applications_by_status}
                  emptyMessage="Aún no hay aplicaciones registradas."
                />
              </div>
              <div>
                <p className="text-text-secondary text-xs font-medium mb-2">Entrevistas por Resultado</p>
                <BreakdownBar data={overview.interviews_by_result} emptyMessage="Aún no hay entrevistas registradas." />
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Networking"
            subtitle="Conversión de contacto a oportunidad - no solo cuántos contactos hay"
            icon={Handshake}
          >
            <div className="mb-6">
              <KpiRow kpis={overview.networking_kpis} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <p className="text-text-secondary text-xs font-medium mb-2">Contactos por Estado</p>
                <BreakdownPie data={overview.networking_by_status} emptyMessage="Aún no hay contactos registrados." />
              </div>
              <div>
                <p className="text-text-secondary text-xs font-medium mb-2">Actividades Realizadas por Categoría</p>
                <BreakdownBar
                  data={overview.networking_activities_by_category}
                  emptyMessage="Aún no hay actividades de networking registradas."
                />
              </div>
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  )
}
