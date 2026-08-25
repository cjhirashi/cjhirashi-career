import { QueryClient } from '@tanstack/react-query'

/**
 * Query-key prefixes for every Admin Panel view that reads a table
 * (career CRUD, PDF styles/templates, LinkedIn, files, agent tasks, …).
 *
 * After Agent Bedrock writes, the open screen must refetch immediately —
 * `staleTime` on the root QueryClient would otherwise keep showing the
 * snapshot from when the user opened the record.
 */
export const ADMIN_DATA_QUERY_PREFIXES = [
  ['career'],
  ['pdf-templates'],
  ['pdf-template-styles'],
  ['fk-options'],
  ['linkedin'],
  ['files'],
  ['agent-tasks'],
  ['github-repos'],
  ['job-providers'],
  ['target-roles'],
  ['bedrock', 'audit-log'],
  ['bedrock', 'memory'],
  ['bedrock', 'tools'],
  ['bedrock', 'usage-metrics'],
  ['bedrock', 'instructions'],
  ['bedrock', 'agent-profiles'],
] as const

export function invalidateAdminDataViews(queryClient: QueryClient): Promise<void> {
  return Promise.all(
    ADMIN_DATA_QUERY_PREFIXES.map((queryKey) =>
      queryClient.invalidateQueries({ queryKey: [...queryKey] })
    )
  ).then(() => undefined)
}
