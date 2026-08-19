/** Parses a project/experience's free-form `metrics` JSON (admin-edited:
 * either {label: value} or [{label, value}]) into a clean [label, value][]
 * list. Returns [] silently if the shape doesn't match either convention
 * rather than crashing on whatever the admin typed. */
export const parseMetrics = (metrics: Record<string, unknown> | unknown[] | null | undefined): [string, unknown][] => {
  if (!metrics) return []

  if (Array.isArray(metrics)) {
    return metrics
      .filter((m): m is { label: unknown; value: unknown } => typeof m === 'object' && m !== null && 'label' in m)
      .map(m => [String((m as { label: unknown }).label), (m as { value: unknown }).value])
  }

  if (typeof metrics === 'object') {
    return Object.entries(metrics)
  }

  return []
}
