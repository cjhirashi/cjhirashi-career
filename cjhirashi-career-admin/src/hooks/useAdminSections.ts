import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminSectionsApi } from '@/api/adminSections'
import { AdminSectionUpdate } from '@/types/adminSections'

export function useAdminSections() {
  return useQuery({
    queryKey: ['admin', 'sections'],
    queryFn: adminSectionsApi.list,
    staleTime: 60_000,
  })
}

export function useAdminSection(sectionId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'sections', sectionId],
    queryFn: () => adminSectionsApi.get(sectionId as string),
    enabled: Boolean(sectionId),
  })
}

export function useAdminSectionUpdate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sectionId, payload }: { sectionId: string; payload: AdminSectionUpdate }) =>
      adminSectionsApi.update(sectionId, payload),
    onSuccess: (_data, { sectionId }) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'sections'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'sections', sectionId] })
      queryClient.invalidateQueries({ queryKey: ['bedrock', 'agent-catalog'] })
    },
  })
}
