import { useMemo } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { careerApi } from '@/api/career'
import { filesApi } from '@/api/files'
import { pdfTemplatesApi } from '@/api/pdfTemplates'
import { pdfTemplateStylesApi } from '@/api/pdfTemplateStyles'
import { bedrockApi } from '@/api/bedrock'
import { agentTasksApi } from '@/api/agentTasks'
import { adminNavTreeApi, adminViewsApi } from '@/api/adminSections'
import { NavGroup, flattenNavTree } from '@/types/adminSections'
import { useNavTree } from '@/hooks/useNavTree'
import { errorReportsApi } from '@/api/errorReports'
import { CAREER_RESOURCES, isTableResource } from '@/config/careerResources'
import { careerQueryKey } from '@/hooks/useCareerResource'

const STALE_MS = 30_000

const countQueryOptions = {
  staleTime: STALE_MS,
  refetchOnWindowFocus: false,
}

/**
 * Table career resource keys (`career-*` sections whose config isn't a
 * singleton) belonging to a nav-tree group, in the group's own section
 * order. Replaces the old `CAREER_DOMAINS`-driven `tableResourceKeysForDomain`
 * now that group membership is data (ADR-023), not a hardcoded map.
 */
export function tableResourceKeysForGroup(
  groupSystemName: string | null,
  groups: NavGroup[] | undefined
): string[] {
  if (!groupSystemName || !groups) return []
  const group = groups.find((g) => g.system_name === groupSystemName)
  if (!group) return []
  return group.sections
    .filter((section) => section.system_name.startsWith('career-'))
    .map((section) => section.system_name.replace(/^career-/, ''))
    .filter((key) => isTableResource(CAREER_RESOURCES[key]))
}

/**
 * Record counts for sidebar table sections. Career counts load only for the
 * expanded group (keyed by the nav-tree group's `system_name`); files/tasks
 * always (pinned top-level tables); agent/settings tables only when their
 * accordion is open. Query keys match the list pages so mutations refresh
 * the badges without a second round trip.
 */
export function useSidebarCounts(expandedDomain: string | null) {
  const { data: navTree } = useNavTree()
  const groups = navTree?.groups
  const careerKeys = useMemo(
    () => tableResourceKeysForGroup(expandedDomain, groups),
    [expandedDomain, groups]
  )
  const loadAgent = expandedDomain === 'agent-ai'
  const loadSettings = expandedDomain === 'settings'

  const careerQueries = useQueries({
    queries: careerKeys.map((key) => ({
      queryKey: careerQueryKey(key, { count: true }),
      queryFn: () => careerApi.count(key),
      ...countQueryOptions,
    })),
  })

  const filesQuery = useQuery({
    queryKey: ['files', { count: true }],
    queryFn: () => filesApi.count(),
    ...countQueryOptions,
  })

  const tasksQuery = useQuery({
    queryKey: ['agent-tasks', { count: true }],
    queryFn: agentTasksApi.count,
    ...countQueryOptions,
  })

  const pdfTemplatesQuery = useQuery({
    queryKey: ['pdf-templates', { count: true }],
    queryFn: async () => (await pdfTemplatesApi.list({ skip: 0, limit: 100 })).length,
    enabled: loadAgent,
    ...countQueryOptions,
  })

  const pdfStylesQuery = useQuery({
    queryKey: ['pdf-template-styles', { count: true }],
    queryFn: async () => (await pdfTemplateStylesApi.list({ skip: 0, limit: 100 })).length,
    enabled: loadAgent,
    ...countQueryOptions,
  })

  const catalogQuery = useQuery({
    queryKey: ['bedrock', 'agent-catalog'],
    queryFn: bedrockApi.listAgentCatalog,
    enabled: loadAgent || loadSettings,
    ...countQueryOptions,
  })

  const navTreeCountsQuery = useQuery({
    queryKey: ['admin', 'nav-tree'],
    queryFn: adminNavTreeApi.get,
    enabled: loadSettings,
    ...countQueryOptions,
  })
  const sectionsCount = navTreeCountsQuery.data
    ? flattenNavTree(navTreeCountsQuery.data).length
    : undefined

  const viewsQuery = useQuery({
    queryKey: ['admin', 'views', {}],
    queryFn: () => adminViewsApi.list(),
    enabled: loadSettings,
    ...countQueryOptions,
  })

  const errorReportsQuery = useQuery({
    queryKey: ['error-reports', 'summary'],
    queryFn: errorReportsApi.summary,
    enabled: loadSettings,
    ...countQueryOptions,
  })

  const toolsQuery = useQuery({
    queryKey: ['bedrock', 'tools'],
    queryFn: bedrockApi.listTools,
    enabled: loadAgent,
    ...countQueryOptions,
  })

  const methodologiesQuery = useQuery({
    queryKey: careerQueryKey('operational-methodologies', { count: true }),
    queryFn: () => careerApi.count('operational-methodologies'),
    enabled: loadAgent,
    ...countQueryOptions,
  })

  const career: Record<string, number | undefined> = {}
  careerKeys.forEach((key, index) => {
    career[key] = careerQueries[index]?.data
  })

  return {
    career,
    pinned: {
      files: filesQuery.data,
      tasks: tasksQuery.data,
    },
    files: filesQuery.data,
    tasks: tasksQuery.data,
    agent: {
      pdfTemplates: pdfTemplatesQuery.data,
      pdfStyles: pdfStylesQuery.data,
      methodologies: methodologiesQuery.data,
      tools: toolsQuery.data?.length,
    },
    settings: {
      catalog: catalogQuery.data?.length,
      sections: sectionsCount,
      views: viewsQuery.data?.length,
      errorsPending: errorReportsQuery.data?.pending,
    },
  }
}
