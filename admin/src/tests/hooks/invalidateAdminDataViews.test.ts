import { describe, it, expect } from 'vitest'
import { QueryClient } from '@tanstack/react-query'
import { ADMIN_DATA_QUERY_PREFIXES, invalidateAdminDataViews } from '@/hooks/invalidateAdminDataViews'

describe('invalidateAdminDataViews', () => {
  it('covers career, PDF, LinkedIn, files and agent table prefixes', () => {
    const keys = ADMIN_DATA_QUERY_PREFIXES.map((prefix) => prefix.join('/'))
    expect(keys).toEqual(
      expect.arrayContaining([
        'career',
        'pdf-templates',
        'pdf-template-styles',
        'linkedin',
        'files',
        'agent-tasks',
      ])
    )
  })

  it('marks matching queries stale so the open view refetches', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    queryClient.setQueryData(['pdf-template-styles', { skip: 0 }], [{ id: 'pds-1', style_guide: null }])
    queryClient.setQueryData(['career', 'competencies', { skip: 0 }], [{ id: 'cmp-1' }])

    await invalidateAdminDataViews(queryClient)

    const styleState = queryClient.getQueryState(['pdf-template-styles', { skip: 0 }])
    const careerState = queryClient.getQueryState(['career', 'competencies', { skip: 0 }])
    expect(styleState?.isInvalidated).toBe(true)
    expect(careerState?.isInvalidated).toBe(true)
  })
})
