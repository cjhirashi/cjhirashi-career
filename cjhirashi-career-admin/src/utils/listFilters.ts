import { ListFilters } from '@/api/career'

export const FILTERABLE_FIELD_TYPES = [
  'select',
  'creatable-select',
  'fk-select',
  'multi-select',
  'fk-multi-select',
  'boolean',
] as const

/** Payload-only fields that are not SQL columns — the list API cannot filter them. */
export const NON_COLUMN_FILTER_FIELDS = new Set(['achievement_ids'])

export function hasActiveFilters(filters: ListFilters | undefined): boolean {
  if (!filters) return false
  return Object.values(filters).some((value) => (Array.isArray(value) ? value.length > 0 : value !== '' && value != null))
}

/** Client-side counterpart of CareerRepository._apply_filters (PDF lists). */
export function recordMatchesFilters(item: Record<string, unknown>, filters?: ListFilters): boolean {
  if (!filters || !hasActiveFilters(filters)) return true
  for (const [key, raw] of Object.entries(filters)) {
    const current = item[key]
    if (Array.isArray(raw)) {
      if (raw.length === 0) continue
      const haystack = Array.isArray(current) ? current.map(String) : [String(current ?? '')]
      if (!raw.some((value) => haystack.includes(String(value)))) return false
      continue
    }
    if (raw === true || raw === false || raw === 'true' || raw === 'false') {
      const wanted = raw === true || raw === 'true'
      if (Boolean(current) !== wanted) return false
      continue
    }
    if (raw === '' || raw == null) continue
    if (String(current ?? '') !== String(raw)) return false
  }
  return true
}
