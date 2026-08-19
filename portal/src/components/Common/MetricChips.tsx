interface MetricChipsProps {
  metrics: Record<string, unknown> | unknown[] | null | undefined
  limit?: number
}

/** Renders a project/experience's `metrics` JSON (admin-edited free-form:
 * either {label: value} or [{label, value}]) as small stat chips. Skips
 * silently if the shape doesn't match either convention rather than
 * crashing on whatever the admin typed. */
export const MetricChips = ({ metrics, limit = 4 }: MetricChipsProps) => {
  if (!metrics) return null

  let entries: [string, unknown][] = []
  if (Array.isArray(metrics)) {
    entries = metrics
      .filter((m): m is { label: unknown; value: unknown } => typeof m === 'object' && m !== null && 'label' in m)
      .map(m => [String((m as { label: unknown }).label), (m as { value: unknown }).value])
  } else if (typeof metrics === 'object') {
    entries = Object.entries(metrics)
  }

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
