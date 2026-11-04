import React, { useMemo } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { TrendingUp } from 'lucide-react'
import { CHART_COLORS, EmptyState, SectionCard, axisTickStyle } from '@/components/career/MetricsCharts'
import type { PortalTrendResponse } from '@/types/portalAnalytics'
import { buildTrendRows } from './format'

const KIND_LABEL = { blog_post: 'Post', application: 'Postulación', deploy: 'Despliegue', other: 'Nota' } as const

interface Props {
  trend: PortalTrendResponse
  comparing: boolean
}

/** RF-061: línea de visitas con el tramo en curso punteado, periodo comparado y anotaciones. */
export const TrendChart: React.FC<Props> = ({ trend, comparing }) => {
  const rows = useMemo(() => buildTrendRows(trend.points, trend.incomplete_from), [trend])
  const days = new Set(rows.map((r) => r.bucket))
  const annotations = trend.annotations.filter((a) => days.has(a.day))

  return (
    <SectionCard title="Visitas en el tiempo" subtitle="Visitas por día. La línea punteada es el periodo aún en curso." icon={TrendingUp}>
      {rows.length === 0 ? (
        <EmptyState message="Aún no hay visitas registradas en este rango." />
      ) : (
        <>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={rows} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="bucket" tick={axisTickStyle} minTickGap={24} />
              <YAxis allowDecimals={false} tick={axisTickStyle} />
              <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-secondary)' }} />
              {annotations.map((a) => (
                <ReferenceLine key={`${a.day}-${a.title}`} x={a.day} stroke="var(--warning-text)" strokeDasharray="2 4" />
              ))}
              {comparing && (
                <Line type="monotone" dataKey="previous" name="Periodo comparado" stroke="#64748b" strokeWidth={1.5} strokeDasharray="4 4" dot={false} connectNulls />
              )}
              <Line type="monotone" dataKey="visits" name="Visitas" stroke={CHART_COLORS[0]} strokeWidth={2} dot={false} connectNulls={false} />
              <Line type="monotone" dataKey="visitsIncomplete" name="En curso" stroke={CHART_COLORS[0]} strokeWidth={2} strokeDasharray="5 4" dot={false} legendType="none" />
            </LineChart>
          </ResponsiveContainer>
          {annotations.length > 0 && (
            <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-text-secondary" aria-label="Anotaciones">
              {annotations.map((a) => (
                <li key={`${a.day}-${a.title}`}>
                  <span className="font-medium text-text">{a.day}</span> · {KIND_LABEL[a.kind]}: {a.title}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </SectionCard>
  )
}
