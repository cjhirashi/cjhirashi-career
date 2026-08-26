import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ListParams } from '@/api/career'
import { pdfTemplatesApi } from '@/api/pdfTemplates'
import { CareerEntity } from '@/types/career'
import { recordMatchesFilters } from '@/utils/listFilters'

export const pdfTemplateQueryKey = (extra?: unknown) =>
  extra === undefined ? (['pdf-templates'] as const) : (['pdf-templates', extra] as const)

const compareValues = (a: unknown, b: unknown, dir: 'asc' | 'desc'): number => {
  const av = a ?? ''
  const bv = b ?? ''
  const cmp =
    typeof av === 'boolean' && typeof bv === 'boolean'
      ? Number(av) - Number(bv)
      : String(av).localeCompare(String(bv), 'es', { sensitivity: 'base' })
  return dir === 'asc' ? cmp : -cmp
}

/** Max page size allowed by `GET /pdf-templates` (backend caps at 100). */
const PDF_TEMPLATE_FETCH_LIMIT = 100

/** Client-side search/sort/pagination over the full template list — the
 * `/pdf-templates` API has no server-side search yet, and the dataset is
 * small enough for this to stay responsive. */
export function usePdfTemplateList(params: ListParams = {}, enabled = true) {
  const { skip = 0, limit = 20, sortBy, sortDir = 'asc', search, filters } = params
  return useQuery({
    queryKey: pdfTemplateQueryKey({ skip, limit, sortBy, sortDir, search, filters }),
    queryFn: async (): Promise<CareerEntity[]> => {
      const all = await pdfTemplatesApi.list({ skip: 0, limit: PDF_TEMPLATE_FETCH_LIMIT })
      let filtered = all as unknown as Record<string, unknown>[]
      if (search) {
        const q = search.toLowerCase()
        filtered = filtered.filter(
          (item) =>
            String(item.title ?? '').toLowerCase().includes(q) ||
            String(item.slug ?? '').toLowerCase().includes(q) ||
            String(item.document_type ?? '').toLowerCase().includes(q) ||
            String(item.description ?? '').toLowerCase().includes(q)
        )
      }
      filtered = filtered.filter((item) => recordMatchesFilters(item, filters))
      if (sortBy) {
        filtered = [...filtered].sort((a, b) =>
          compareValues(a[sortBy], b[sortBy], sortDir)
        )
      }
      return filtered.slice(skip, skip + limit) as CareerEntity[]
    },
    enabled,
  })
}

export function usePdfTemplateCount(params: Pick<ListParams, 'search' | 'filters'> = {}, enabled = true) {
  const { search, filters } = params
  return useQuery({
    queryKey: pdfTemplateQueryKey({ count: true, search, filters }),
    queryFn: async () => {
      const all = await pdfTemplatesApi.list({ skip: 0, limit: PDF_TEMPLATE_FETCH_LIMIT })
      let filtered = all as unknown as Record<string, unknown>[]
      if (search) {
        const q = search.toLowerCase()
        filtered = filtered.filter(
          (item) =>
            String(item.title ?? '').toLowerCase().includes(q) ||
            String(item.slug ?? '').toLowerCase().includes(q) ||
            String(item.document_type ?? '').toLowerCase().includes(q) ||
            String(item.description ?? '').toLowerCase().includes(q)
        )
      }
      return filtered.filter((item) => recordMatchesFilters(item, filters)).length
    },
    enabled,
  })
}

export function usePdfTemplateMutations() {
  const queryClient = useQueryClient()

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: pdfTemplateQueryKey(), exact: false })

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      pdfTemplatesApi.create(payload) as Promise<CareerEntity>,
    onSuccess: invalidate,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      pdfTemplatesApi.update(id, payload) as Promise<CareerEntity>,
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => pdfTemplatesApi.remove(id),
    onSuccess: invalidate,
  })

  return { createMutation, updateMutation, deleteMutation }
}
