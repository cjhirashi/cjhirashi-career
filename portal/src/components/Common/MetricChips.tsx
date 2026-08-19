import { parseMetrics } from '@/utils/metrics'

interface MetricChipsProps {
  metrics: Record<string, unknown> | unknown[] | null | undefined
  limit?: number
}

/** Renders a project/experience's `metrics` JSON as small stat chips. */
export const MetricChips = ({ metrics, limit = 4 }: MetricChipsProps) => {
  const entries = parseMetrics(metrics)
  if (entries.length === 0) return null

  return (
    <div className="flex flex-wrap gap-3">
      {entries.slice(0, limit).map(([label, value]) => (
        <div key={label} className="text-center">
          <div className="text-lg font-bold text-primary mono">{String(value)}</div>
          <div className="text-xs text-text-secondary">{label}</div>
        </div>
      ))}
    </div>
  )
}
