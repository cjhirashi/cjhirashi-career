import React from 'react'
import { EmptyState } from '@/components/career/MetricsCharts'
import type { PortalBreakdownRow } from '@/types/portalAnalytics'
import { CHANNEL_LABELS, formatDuration, formatNumber, formatRate } from './format'

interface Props {
  rows: PortalBreakdownRow[]
  keyLabel: string
  translateChannel?: boolean
  emptyMessage?: string
}

export const BreakdownTable: React.FC<Props> = ({ rows, keyLabel, translateChannel, emptyMessage = 'Sin datos en este rango.' }) => {
  if (rows.length === 0) return <EmptyState message={emptyMessage} />
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-text-secondary text-xs">
            <th className="py-2 pr-3 font-medium min-w-[8rem]">{keyLabel}</th>
            <th className="py-2 px-2 font-medium text-right">Visitantes</th>
            <th className="py-2 px-2 font-medium text-right">Visitas</th>
            <th className="py-2 px-2 font-medium text-right">%</th>
            <th className="py-2 px-2 font-medium text-right">Rebote</th>
            <th className="py-2 pl-2 font-medium text-right">Mediana</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const raw = row.key ?? 'Desconocido'
            return (
              <tr key={raw} className="border-t border-border">
                <td className="py-2 pr-3 text-text min-w-[8rem]">{translateChannel ? (CHANNEL_LABELS[raw] ?? raw) : raw}</td>
                <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatNumber(row.visitors)}</td>
                <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatNumber(row.visits)}</td>
                <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatRate(row.share)}</td>
                <td className="py-2 px-2 text-right mono whitespace-nowrap">{formatRate(row.bounce_rate)}</td>
                <td className="py-2 pl-2 text-right mono whitespace-nowrap">{formatDuration(row.median_active_ms)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
