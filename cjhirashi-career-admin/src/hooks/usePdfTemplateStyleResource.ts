import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ListParams } from '@/api/career'
import { pdfTemplateStylesApi } from '@/api/pdfTemplateStyles'
import { CareerEntity } from '@/types/career'
import { recordMatchesFilters } from '@/utils/listFilters'

export const pdfTemplateStyleQueryKey = (extra?: unknown) =>
  extra === undefined ? (['pdf-template-styles'] as const) : (['pdf-template-styles', extra] as const)

const PDF_STYLE_FETCH_LIMIT = 100

const compareValues = (a: unknown, b: unknown, dir: 'asc' | 'desc'): number => {
  const av = a ?? ''
  const bv = b ?? ''
  const cmp =
    typeof av === 'boolean' && typeof bv === 'boolean'
      ? Number(av) - Number(bv)
      : String(av).localeCompare(String(bv), 'es', { sensitivity: 'base' })
  return dir === 'asc' ? cmp : -cmp
}

export function usePdfTemplateStyleList(params: ListParams = {}, enabled = true) {
  const { skip = 0, limit = 20, sortBy, sortDir = 'asc', search, filters } = params
  return useQuery({
    queryKey: pdfTemplateStyleQueryKey({ skip, limit, sortBy, sortDir, search, filters }),
    queryFn: async (): Promise<CareerEntity[]> => {
      const all = await pdfTemplateStylesApi.list({ skip: 0, limit: PDF_STYLE_FETCH_LIMIT })
      let filtered = all as unknown as Record<string, unknown>[]
      if (search) {
        const q = search.toLowerCase()
        filtered = filtered.filter(
          (item) =>
            String(item.title ?? '').toLowerCase().includes(q) ||
            String(item.slug ?? '').toLowerCase().includes(q) ||
            String(item.description ?? '').toLowerCase().includes(q)
        )
      }
      filtered = filtered.filter((item) => recordMatchesFilters(item, filters))
      if (sortBy) {
        filtered = [...filtered].sort((a, b) => compareValues(a[sortBy], b[sortBy], sortDir))
      }
      return filtered.slice(skip, skip + limit) as CareerEntity[]
    },
    enabled,
  })
}

export function usePdfTemplateStyleCount(params: Pick<ListParams, 'search' | 'filters'> = {}, enabled = true) {
  const { search, filters } = params
  return useQuery({
    queryKey: pdfTemplateStyleQueryKey({ count: true, search, filters }),
    queryFn: async () => {
      const all = await pdfTemplateStylesApi.list({ skip: 0, limit: PDF_STYLE_FETCH_LIMIT })
      let filtered = all as unknown as Record<string, unknown>[]
      if (search) {
        const q = search.toLowerCase()
        filtered = filtered.filter(
          (item) =>
            String(item.title ?? '').toLowerCase().includes(q) ||
            String(item.slug ?? '').toLowerCase().includes(q) ||
            String(item.description ?? '').toLowerCase().includes(q)
        )
      }
      return filtered.filter((item) => recordMatchesFilters(item, filters)).length
    },
    enabled,
  })
}

export function usePdfTemplateStyleMutations() {
  const queryClient = useQueryClient()

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: pdfTemplateStyleQueryKey(), exact: false })

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      pdfTemplateStylesApi.create(payload) as Promise<CareerEntity>,
    onSuccess: invalidate,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      pdfTemplateStylesApi.update(id, payload) as Promise<CareerEntity>,
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => pdfTemplateStylesApi.remove(id),
    onSuccess: invalidate,
  })

  return { createMutation, updateMutation, deleteMutation }
}
