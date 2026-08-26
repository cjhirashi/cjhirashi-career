import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { careerApi } from '@/api/career'
import { SelectOption } from '@/config/careerResources'
import { careerQueryKey } from '@/hooks/useCareerResource'

/**
 * Unique values already saved in a career-resource column. Nested under the
 * same `careerQueryKey(resource)` prefix as the list, so create/update
 * invalidation refreshes the option list for the next record.
 */
export function useColumnOptions(
  resource: string,
  field: string
): { options: SelectOption[]; isLoading: boolean; isError: boolean } {
  const { data, isLoading, isError } = useQuery<string[]>({
    queryKey: careerQueryKey(resource, { distinct: field }),
    queryFn: () => careerApi.distinct(resource, field),
    enabled: Boolean(resource && field),
    staleTime: 30 * 1000,
  })

  const options = useMemo<SelectOption[]>(() => {
    if (!data) return []
    return data.map((value) => ({ value, label: value }))
  }, [data])

  return { options, isLoading, isError }
}
