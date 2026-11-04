import React from 'react'
import { Route, Repeat } from 'lucide-react'
import { EmptyState, SectionCard } from '@/components/career/MetricsCharts'
import { usePortalPaths, usePortalRetention } from '@/hooks/usePortalAnalytics'
import type { PortalQuery } from '@/types/portalAnalytics'
import { formatNumber, shortPath } from './format'

const cellShade = (ratio: number) => ({ background: `color-mix(in srgb, var(--primary-color) ${Math.round(ratio * 70)}%, transparent)` })

export const PathsRetention: React.FC<{ query: PortalQuery }> = ({ query }) => {
  const paths = usePortalPaths(query)
  const retention = usePortalRetention(query)
  const weeks = Math.max(0, ...(retention.data?.rows.map((r) => r.active_by_week.length) ?? [0]))

  return (
    <div className="grid grid-cols-1 2xl:grid-cols-2 gap-6">
      <SectionCard title="Recorridos" subtitle="De qué página pasan a cuál" icon={Route}>
        {!paths.data || paths.data.rows.length === 0 ? (
          <EmptyState message="Aún no hay visitas con más de una página." />
        ) : (
          <ul className="space-y-2 text-sm">
            {paths.data.rows.map((p) => (
              <li key={`${p.from_page}->${p.to_page}`} className="flex items-center justify-between gap-3">
                <span className="text-text break-all" title={`${p.from_page} → ${p.to_page}`}>
                  {shortPath(p.from_page, 24)} <span className="text-text-secondary">→</span> {shortPath(p.to_page, 24)}
                </span>
                <span className="mono text-text-secondary">{formatNumber(p.count)}</span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>

      <SectionCard title="Retención semanal" subtitle="Cuántos visitantes de cada semana vuelven en las siguientes" icon={Repeat}>
        {!retention.data || retention.data.rows.length === 0 ? (
          <EmptyState message="Aún no hay cohortes suficientes." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-center">
              <thead>
                <tr className="text-text-secondary text-xs">
                  <th className="py-2 pr-3 font-medium text-left">Semana</th>
                  <th className="py-2 px-2 font-medium">Tamaño</th>
                  {Array.from({ length: weeks }, (_, n) => (
                    <th key={n} className="py-2 px-2 font-medium">{n === 0 ? 'Sem. 0' : `+${n}`}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {retention.data.rows.map((row) => (
                  <tr key={row.cohort_week} className="border-t border-border">
                    <td className="py-2 pr-3 text-left text-text whitespace-nowrap">{row.cohort_week}</td>
                    <td className="py-2 px-2 mono">{formatNumber(row.size)}</td>
                    {row.active_by_week.map((count, n) => (
                      <td key={n} className="py-2 px-2 mono whitespace-nowrap" style={cellShade(row.size ? count / row.size : 0)} title={`${count} de ${row.size}`}>
                        {row.size ? `${Math.round((count / row.size) * 100)} %` : '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  )
}
