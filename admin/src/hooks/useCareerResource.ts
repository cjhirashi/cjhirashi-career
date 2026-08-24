import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { careerApi, ListParams } from '@/api/career'
import { CareerEntity, SearchOverview, WeeklySearchMetrics } from '@/types/career'

/**
 * Generic React Query wrapper around `careerApi` for a single career-domain
 * resource (e.g. "projects", "vacancies"). Used by `CareerResourceView` so
 * every resource shares the same fetching/caching/mutation behaviour instead
 * of hand-rolling a hook per module.
 */
export const careerQueryKey = (resource: string, extra?: unknown) =>
  extra === undefined ? (['career', resource] as const) : (['career', resource, extra] as const)

export function useCareerList<T = CareerEntity>(resource: string, params: ListParams = {}, enabled = true) {
  const { skip = 0, limit = 20, sortBy, sortDir, search } = params
  return useQuery({
    queryKey: careerQueryKey(resource, { skip, limit, sortBy, sortDir, search }),
    queryFn: () => careerApi.list<T>(resource, { skip, limit, sortBy, sortDir, search }),
    enabled,
  })
}

/** Total row count for a resource, independent of pagination - shown next
 * to the table's title. Nested under the same `careerQueryKey(resource)`
 * prefix as the list query, so `useCareerMutations`'s invalidation (which
 * uses `exact: false`) refreshes it too after a create/delete. */
export function useCareerCount(resource: string, enabled = true) {
  return useQuery({
    queryKey: careerQueryKey(resource, { count: true }),
    queryFn: () => careerApi.count(resource),
    enabled,
  })
}

export function useCareerMutations<T = CareerEntity>(resource: string) {
  const queryClient = useQueryClient()

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: careerQueryKey(resource), exact: false })

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => careerApi.create<T>(resource, payload),
    onSuccess: invalidate,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      careerApi.update<T>(resource, id, payload),
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => careerApi.remove(resource, id),
    onSuccess: invalidate,
  })

  return { createMutation, updateMutation, deleteMutation }
}

/**
 * Weekly search-activity metrics (`GET /career/metrics/weekly`), backed by a
 * read-only SQL view - no mutations here, just a query.
 */
export function useWeeklyMetrics(limit = 12) {
  return useQuery<WeeklySearchMetrics[]>({
    queryKey: careerQueryKey('metrics-weekly', { limit }),
    queryFn: () => careerApi.weeklyMetrics(limit),
  })
}

/**
 * Aggregated snapshot across the 12 Operativa de Búsqueda tables
 * (`GET /career/metrics/search-overview`) - powers the search-strategy
 * dashboard's charts. Computed live server-side, no mutations here.
 */
export function useSearchOverview() {
  return useQuery<SearchOverview>({
    queryKey: careerQueryKey('metrics-search-overview'),
    queryFn: () => careerApi.searchOverview(),
  })
}
