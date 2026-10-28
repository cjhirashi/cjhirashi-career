import React from 'react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, Legend } from 'recharts'

/** Fixed palette reusing the app's theme tokens (adapts light/dark
 * automatically, same as badges elsewhere) plus a few neutral fallbacks for
 * breakdowns with more categories than semantic colors (e.g. 5 role
 * categories, 6+ track categories). Shared by every metrics dashboard
 * (Búsqueda, Portal) so they stay visually consistent. */
export const CHART_COLORS = [
  'var(--primary-color)',
  'var(--success-text)',
  'var(--warning-text)',
  'var(--error-text)',
  '#8b5cf6',
  '#ec4899',
  '#64748b',
  '#0ea5e9',
]

export const axisTickStyle = { fill: 'var(--text-secondary)', fontSize: 12 }

export const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <p className="text-text-secondary text-sm text-center py-10">{message}</p>
)

export interface Breakdown {
  label: string
  count: number
}

export const BreakdownPie: React.FC<{ data: Breakdown[]; emptyMessage: string }> = ({ data, emptyMessage }) => {
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

export const BreakdownBar: React.FC<{ data: Breakdown[]; emptyMessage: string }> = ({ data, emptyMessage }) => {
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

/** A rate, not a raw count - the "¿vamos bien?" card. `valuePercentage` null
 * renders "—" instead of a misleading 0% when there's no data yet (e.g. 0/0). */
export const KpiCard: React.FC<{ label: string; valuePercentage: number | null; detail?: string | null }> = ({
  label,
  valuePercentage,
  detail,
}) => (
  <div className="stat-card">
    <p className="text-text-secondary text-sm font-medium">{label}</p>
    <p className="text-3xl font-bold text-text mono mt-2">{valuePercentage !== null ? `${valuePercentage}%` : '—'}</p>
    {detail && <p className="text-text-secondary text-xs mt-1">{detail}</p>}
  </div>
)

/** Progress toward a numeric target, e.g. CVs enviados vs. la meta del plan
 * de búsqueda activo - "¿se está cumpliendo el objetivo?", not just el dato.
 * A compact bullet graph (Stephen Few, 2006): a thick bar for the actual
 * value plus a thin tick mark for the target, instead of a plain progress
 * bar that hides whether the target itself has already been reached. */
export const TargetProgress: React.FC<{ label: string; actual: number; target: number }> = ({
  label,
  actual,
  target,
}) => {
  const onTrack = target === 0 || actual >= target
  // Headroom past the target (or the actual, if it overshot) so the tick
  // mark never sits flush against the edge.
  const domain = Math.max(actual, target, 1) * 1.15
  const barPct = Math.min(100, (actual / domain) * 100)
  const targetPct = Math.min(100, (target / domain) * 100)
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="text-text-secondary">{label}</span>
        <span className="text-text font-semibold mono">
          {actual} / {target}
        </span>
      </div>
      <div className="relative w-full h-3 rounded-sm bg-glass overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-sm"
          style={{ width: `${barPct}%`, background: onTrack ? 'var(--success-text)' : 'var(--primary-color)' }}
        />
        {target > 0 && (
          <div
            className="absolute inset-y-0 w-0.5"
            style={{ left: `${targetPct}%`, background: 'var(--text)' }}
            title={`Meta: ${target}`}
          />
        )}
      </div>
    </div>
  )
}

export const SectionCard: React.FC<{
  title: string
  subtitle?: string
  icon: React.ElementType
  children: React.ReactNode
}> = ({ title, subtitle, icon: Icon, children }) => (
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
