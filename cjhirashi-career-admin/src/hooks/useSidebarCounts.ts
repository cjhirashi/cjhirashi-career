import { useMemo } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { careerApi } from '@/api/career'
import { filesApi } from '@/api/files'
import { pdfTemplatesApi } from '@/api/pdfTemplates'
import { pdfTemplateStylesApi } from '@/api/pdfTemplateStyles'
import { bedrockApi } from '@/api/bedrock'
import { agentTasksApi } from '@/api/agentTasks'
import { adminSectionsApi } from '@/api/adminSections'
import { CAREER_DOMAINS, CAREER_RESOURCES, isTableResource } from '@/config/careerResources'
import { careerQueryKey } from '@/hooks/useCareerResource'

const STALE_MS = 30_000

const countQueryOptions = {
  staleTime: STALE_MS,
  refetchOnWindowFocus: false,
}

export function tableResourceKeysForDomain(domainKey: string | null): string[] {
  if (!domainKey) return []
  const domain = CAREER_DOMAINS.find((item) => item.key === domainKey)
  if (!domain) return []
  return domain.resourceKeys.filter((key) => isTableResource(CAREER_RESOURCES[key]))
}

/**
 * Record counts for sidebar table sections. Career counts load only for the
 * expanded domain; files always (top-level table); agent tables when that
 * accordion is open. Query keys match the list pages so mutations refresh
 * the badges without a second round trip.
 */
export function useSidebarCounts(expandedDomain: string | null) {
  const careerKeys = useMemo(() => tableResourceKeysForDomain(expandedDomain), [expandedDomain])
  const loadAgent = expandedDomain === 'agent'
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

  const sectionsQuery = useQuery({
    queryKey: ['admin', 'sections'],
    queryFn: adminSectionsApi.list,
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
      sections: sectionsQuery.data?.length,
    },
  }
}
