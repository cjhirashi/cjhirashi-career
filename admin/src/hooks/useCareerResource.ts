import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { careerApi, ListParams } from '@/api/career'
import { CareerEntity, WeeklySearchMetrics } from '@/types/career'

/**
 * Generic React Query wrapper around `careerApi` for a single career-domain
 * resource (e.g. "projects", "vacancies"). Used by `CareerResourceView` so
 * every resource shares the same fetching/caching/mutation behaviour instead
 * of hand-rolling a hook per module.
 */
export const careerQueryKey = (resource: string, extra?: unknown) =>
  extra === undefined ? (['career', resource] as const) : (['career', resource, extra] as const)

export function useCareerList<T = CareerEntity>(resource: string, params: ListParams = {}) {
  const { skip = 0, limit = 20 } = params
  return useQuery({
    queryKey: careerQueryKey(resource, { skip, limit }),
    queryFn: () => careerApi.list<T>(resource, { skip, limit }),
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
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      careerApi.update<T>(resource, id, payload),
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => careerApi.remove(resource, id),
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
