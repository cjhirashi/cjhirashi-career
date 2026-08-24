import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { careerApi } from '@/api/career'
import { pdfTemplateStylesApi } from '@/api/pdfTemplateStyles'
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

export type FkApiMode = 'career' | 'pdf-template-styles'

async function fetchFkRecords(apiMode: FkApiMode, resource: string): Promise<Record<string, unknown>[]> {
  if (apiMode === 'pdf-template-styles') {
    return pdfTemplateStylesApi.list({ skip: 0, limit: 100 }) as unknown as Record<string, unknown>[]
  }
  return careerApi.list(resource, { limit: 500 })
}

/**
 * Fetches records for a FK selector and converts them to SelectOption[].
 */
export function useFkOptions(
  resource: string | undefined,
  labelField?: string | string[],
  apiMode: FkApiMode = 'career'
): { options: SelectOption[]; isLoading: boolean; isError: boolean } {
  const { data, isLoading, isError } = useQuery<Record<string, unknown>[]>({
    queryKey: ['fk-options', apiMode, resource],
    queryFn: () => fetchFkRecords(apiMode, resource!),
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

export function useFkLabel(
  resource: string | undefined,
  id: string | null | undefined,
  labelField?: string | string[],
  apiMode: FkApiMode = 'career'
): string {
  const { options } = useFkOptions(resource, labelField, apiMode)
  if (!id) return '—'
  const match = options.find((o) => o.value === id)
  return match ? match.label : id
}
