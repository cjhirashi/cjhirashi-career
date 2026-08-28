import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  adminNavTreeApi,
  adminSectionGroupsApi,
  adminSectionsApi,
} from '@/api/adminSections'
import { SectionReorderRequest, SectionReparentRequest } from '@/types/adminSections'

const NAV_TREE_KEY = ['admin', 'nav-tree'] as const
const SECTION_GROUPS_KEY = ['admin', 'section-groups'] as const
const SECTIONS_KEY = ['admin', 'sections'] as const

/** Árbol completo del sidebar (grupos → L1 → L2 → L3, con vistas anidadas). */
export function useNavTree() {
  return useQuery({
    queryKey: NAV_TREE_KEY,
    queryFn: adminNavTreeApi.get,
    staleTime: 60_000,
  })
}

export function useAdminSectionGroups() {
  return useQuery({
    queryKey: SECTION_GROUPS_KEY,
    queryFn: adminSectionGroupsApi.list,
    staleTime: 60_000,
  })
}

function invalidateNavQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: NAV_TREE_KEY })
  queryClient.invalidateQueries({ queryKey: SECTION_GROUPS_KEY })
  queryClient.invalidateQueries({ queryKey: SECTIONS_KEY })
}

export function useAdminSectionGroupReorder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (order: string[]) => adminSectionGroupsApi.reorder(order),
    onSuccess: () => invalidateNavQueries(queryClient),
  })
}

/** Lista una sola tabla de secciones por nivel: 'l1' | 'l2' | 'l3'. */
export function useAdminSectionsByLevel(level: 'l1' | 'l2' | 'l3') {
  return useQuery({
    queryKey: [...SECTIONS_KEY, level],
    queryFn: () => adminSectionsApi.listByLevel(level),
    staleTime: 60_000,
  })
}

export function useAdminSection(sectionId: string | undefined) {
  return useQuery({
    queryKey: [...SECTIONS_KEY, sectionId],
    queryFn: () => adminSectionsApi.get(sectionId as string),
    enabled: Boolean(sectionId),
  })
}

/** Reorden / re-parent de una sección, dentro del mismo nivel. */
export function useAdminSectionUpdate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sectionId, payload }: { sectionId: string; payload: SectionReparentRequest }) =>
      adminSectionsApi.update(sectionId, payload),
    onSuccess: (_data, { sectionId }) => {
      invalidateNavQueries(queryClient)
      queryClient.invalidateQueries({ queryKey: [...SECTIONS_KEY, sectionId] })
    },
  })
}

/** Reorden batch de las secciones hijas de un contenedor (grupo o sección). */
export function useAdminSectionsReorder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SectionReorderRequest) => adminSectionsApi.reorder(payload),
    onSuccess: () => invalidateNavQueries(queryClient),
  })
}
