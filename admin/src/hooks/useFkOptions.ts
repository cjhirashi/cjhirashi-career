import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { careerApi } from '@/api/career'
import { SelectOption } from '@/config/careerResources'

/** Resolves the display label from a record using one or more candidate fields. */
export function resolveFkLabel(
  record: Record<string, unknown>,
  labelField: string | string[] = ['name', 'title', 'role_name', 'pillar_name', 'position_title', 'company']
): string {
  const fields = Array.isArray(labelField) ? labelField : [labelField]
  for (const f of fields) {
    const v = record[f]
    if (v != null && String(v).trim() !== '') return String(v)
  }
  return String(record.id ?? '—')
}

/**
 * Fetches all records from a career resource and converts them to
 * SelectOption[] of the form  "id — Label".
 *
 * Results are cached by react-query under the key ['fk-options', resource].
 * Multiple fields referencing the same resource share a single request.
 */
export function useFkOptions(
  resource: string | undefined,
  labelField?: string | string[]
): { options: SelectOption[]; isLoading: boolean; isError: boolean } {
  const { data, isLoading, isError } = useQuery<Record<string, unknown>[]>({
    queryKey: ['fk-options', resource],
    queryFn: () => careerApi.list(resource!, { limit: 500 }),
    enabled: Boolean(resource),
    staleTime: 2 * 60 * 1000,
  })

  const options = useMemo<SelectOption[]>(() => {
    if (!data) return []
    return data.map((record) => {
      const id = String(record.id ?? '')
      const label = resolveFkLabel(record, labelField)
      return { value: id, label: `${id} — ${label}` }
    })
  }, [data, labelField])

  return { options, isLoading, isError }
}

/**
 * Resolves the display string for a stored FK id using the same cached data.
 * Returns "id — Label" when found, or just "id" as fallback.
 */
export function useFkLabel(
  resource: string | undefined,
  id: string | null | undefined,
  labelField?: string | string[]
): string {
  const { options } = useFkOptions(resource, labelField)
  if (!id) return '—'
  const match = options.find((o) => o.value === id)
  return match ? match.label : id
}
