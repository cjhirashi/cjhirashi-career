import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminViewsApi } from '@/api/adminSections'
import { AdminViewUpdateRequest } from '@/types/adminSections'

const VIEWS_KEY = ['admin', 'views'] as const
const NAV_TREE_KEY = ['admin', 'nav-tree'] as const

export function useAdminViews(filters?: {
  section_id?: string
  responsible?: string
  data_source?: string
}) {
  return useQuery({
    queryKey: [...VIEWS_KEY, filters ?? {}],
    queryFn: () => adminViewsApi.list(filters),
    staleTime: 60_000,
  })
}

export function useAdminView(viewId: string | undefined) {
  return useQuery({
    queryKey: [...VIEWS_KEY, viewId],
    queryFn: () => adminViewsApi.get(viewId as string),
    enabled: Boolean(viewId),
  })
}

export function useAdminViewUpdate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ viewId, payload }: { viewId: string; payload: AdminViewUpdateRequest }) =>
      adminViewsApi.update(viewId, payload),
    onSuccess: (_data, { viewId }) => {
      queryClient.invalidateQueries({ queryKey: VIEWS_KEY })
      queryClient.invalidateQueries({ queryKey: [...VIEWS_KEY, viewId] })
      queryClient.invalidateQueries({ queryKey: NAV_TREE_KEY })
      queryClient.invalidateQueries({ queryKey: ['bedrock', 'agent-catalog'] })
    },
  })
}
