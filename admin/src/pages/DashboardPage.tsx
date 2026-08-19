import React from 'react'
import { Target, FolderOpen, Briefcase, Handshake } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useWeeklyMetrics } from '@/hooks/useCareerResource'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

const formatWeekStart = (value: string | null): string => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' })
}

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  const { data: weeklyMetrics, isLoading: metricsLoading, isError: metricsError, error: metricsErrorObj } =
    useWeeklyMetrics(8)

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
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Total Skills</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">0</p>
            </div>
            <Target size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Add your competencies</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Projects</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">0</p>
            </div>
            <FolderOpen size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Showcase your work</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Positions</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">0</p>
            </div>
            <Briefcase size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Document your experience</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Contacts</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mono mt-2">0</p>
            </div>
            <Handshake size={28} className="text-primary" aria-hidden="true" />
          </div>
          <p className="text-slate-500 dark:text-slate-400 text-xs mt-4">Build your network</p>
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

          {!metricsLoading && !metricsError && (!weeklyMetrics || weeklyMetrics.length === 0) && (
            <p className="text-slate-600 dark:text-slate-400 text-sm text-center py-6">
              Aún no hay actividad de búsqueda registrada.
            </p>
          )}

          {!metricsLoading && !metricsError && weeklyMetrics && weeklyMetrics.length > 0 && (
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

      {/* Getting Started */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Getting Started</h2>
        </div>
        <div className="card-body">
          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 dark:bg-cyan-900/40 rounded-full flex items-center justify-center text-cyan-700 dark:text-cyan-300 font-semibold">
                1
              </div>
              <div>
                <h3 className="font-medium text-slate-900 dark:text-slate-100">Set Your Professional Identity</h3>
                <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
                  Define your IKIGAI, differentiators, and professional narrative
                </p>
                <a href="/identity" className="text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 text-sm font-medium mt-2 inline-block">
                  Go to Identity →
                </a>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 dark:bg-cyan-900/40 rounded-full flex items-center justify-center text-cyan-700 dark:text-cyan-300 font-semibold">
                2
              </div>
              <div>
                <h3 className="font-medium text-slate-900 dark:text-slate-100">Document Your Competencies</h3>
                <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
                  Add technical, transferable, and business skills with proficiency levels
                </p>
                <a href="/competencies" className="text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 text-sm font-medium mt-2 inline-block">
                  Go to Competencies →
                </a>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 dark:bg-cyan-900/40 rounded-full flex items-center justify-center text-cyan-700 dark:text-cyan-300 font-semibold">
                3
              </div>
              <div>
                <h3 className="font-medium text-slate-900 dark:text-slate-100">Showcase Your Evidence</h3>
                <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
                  Add projects, positions, achievements, and STAR cases
                </p>
                <a href="/evidence" className="text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 text-sm font-medium mt-2 inline-block">
                  Go to Evidence →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
