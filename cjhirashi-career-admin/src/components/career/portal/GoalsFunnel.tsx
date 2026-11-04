import React, { useEffect, useState } from 'react'
import { Target } from 'lucide-react'
import { EmptyState, SectionCard } from '@/components/career/MetricsCharts'
import { useCareerList } from '@/hooks/useCareerResource'
import { usePortalFunnel, usePortalGoals } from '@/hooks/usePortalAnalytics'
import type { PortalFunnelDefinition, PortalQuery } from '@/types/portalAnalytics'
import { formatNumber, formatRate } from './format'

const GOAL_TYPE: Record<string, string> = {
  event: 'Evento',
  page: 'Página',
  outbound: 'Enlace saliente',
  min_active: 'Tiempo activo',
  min_pages: 'Páginas vistas',
}

export const GoalsFunnel: React.FC<{ query: PortalQuery }> = ({ query }) => {
  const goals = usePortalGoals(query)
  const funnels = useCareerList<PortalFunnelDefinition>('portal-funnels', { limit: 50 })
  const [funnelId, setFunnelId] = useState<string | null>(null)
  const items = funnels.data ?? []
  useEffect(() => {
    if (!funnelId && items.length > 0) setFunnelId(items[0].id)
  }, [items, funnelId])
  const funnel = usePortalFunnel(query, funnelId)
  const widest = Math.max(1, ...(funnel.data?.steps.map((s) => s.visits) ?? [1]))

  return (
    <div className="grid grid-cols-1 2xl:grid-cols-2 gap-6">
      <SectionCard title="Metas" subtitle="Visitas que cumplieron cada meta" icon={Target}>
        {!goals.data || goals.data.rows.length === 0 ? (
          <EmptyState message="No hay metas configuradas." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-secondary text-xs">
                  <th className="py-2 pr-3 font-medium">Meta</th>
                  <th className="py-2 px-2 font-medium text-right">Visitas</th>
                  <th className="py-2 px-2 font-medium text-right">Visitantes</th>
                  <th className="py-2 pl-2 font-medium text-right">Conversión</th>
                </tr>
              </thead>
              <tbody>
                {goals.data.rows.map((g) => (
                  <tr key={g.goal_id} className="border-t border-border">
                    <td className="py-2 pr-3 text-text">
                      {g.name}
                      <span className="block text-xs text-text-secondary">
                        {GOAL_TYPE[g.type] ?? g.type}
                        {g.is_key_event ? ' · evento clave' : ''}
                      </span>
                    </td>
                    <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatNumber(g.converted_visits)}</td>
                    <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatNumber(g.converting_visitors)}</td>
                    <td className="py-2 pl-2 text-right mono whitespace-nowrap">{formatRate(g.conversion_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Embudo" subtitle="Cuántas visitas avanzan paso a paso, en orden" icon={Target}>
        {items.length === 0 ? (
          <EmptyState message="Aún no hay embudos definidos. Se crean por la API (recurso portal-funnels), por ejemplo desde un agente." />
        ) : (
          <>
            <select className="input-field w-auto mb-4" aria-label="Embudo" value={funnelId ?? ''} onChange={(e) => setFunnelId(e.target.value)}>
              {items.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
            <ol className="space-y-3">
              {(funnel.data?.steps ?? []).map((step, i) => (
                <li key={`${step.label}-${i}`}>
                  <div className="flex justify-between text-sm text-text">
                    <span>
                      {i + 1}. {step.label}
                    </span>
                    <span className="mono">
                      {formatNumber(step.visits)}
                      {i > 0 && <span className="text-text-secondary text-xs"> · {formatRate(step.from_previous)} del paso anterior</span>}
                    </span>
                  </div>
                  <div className="h-2 mt-1 rounded bg-border overflow-hidden" aria-hidden="true">
                    <div className="h-full rounded" style={{ width: `${(step.visits / widest) * 100}%`, background: 'var(--primary-color)' }} />
                  </div>
                </li>
              ))}
            </ol>
          </>
        )}
      </SectionCard>
    </div>
  )
}
