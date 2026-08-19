import { isShortMetric, parseMetrics } from '@/utils/metrics'

interface MetricChipsProps {
  metrics: Record<string, unknown> | unknown[] | null | undefined
  limit?: number
}

/** Renders a project/experience's `metrics` JSON. Short values ("3.5
 * meses", "4 ingenieros") render as compact stat chips; longer
 * achievement-style sentences render as readable rows instead of being
 * forced into the same big/bold/centered treatment. */
export const MetricChips = ({ metrics, limit = 4 }: MetricChipsProps) => {
  const entries = parseMetrics(metrics)
  if (entries.length === 0) return null

  return (
    <div className="flex flex-wrap gap-4">
      {entries.slice(0, limit).map(([label, value]) => {
        const str = String(value)
        return isShortMetric(value) ? (
          <div key={label} className="text-center">
            <div className="text-lg font-bold text-primary mono">{str}</div>
            <div className="text-xs text-text-secondary">{label}</div>
          </div>
        ) : (
          <div key={label} className="w-full">
            <div className="text-sm font-semibold text-primary">{str}</div>
            <div className="text-xs text-text-secondary">{label}</div>
          </div>
        )
      })}
    </div>
  )
}
