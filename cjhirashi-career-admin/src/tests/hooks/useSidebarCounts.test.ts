import { describe, it, expect } from 'vitest'
import { isTableResource, CAREER_RESOURCES } from '@/config/careerResources'
import { tableResourceKeysForDomain } from '@/hooks/useSidebarCounts'

describe('sidebar table resources', () => {
  it('treats list resources as tables and singletons as not', () => {
    expect(isTableResource(CAREER_RESOURCES['work-history'])).toBe(true)
    expect(isTableResource(CAREER_RESOURCES['personal-profile'])).toBe(false)
    expect(isTableResource(CAREER_RESOURCES.identity)).toBe(false)
    expect(isTableResource(undefined)).toBe(false)
  })

  it('returns only table keys for a domain, in declared order', () => {
    expect(tableResourceKeysForDomain('digital')).toEqual(['publications'])
    expect(tableResourceKeysForDomain('support')).toEqual(['tags'])
    expect(tableResourceKeysForDomain(null)).toEqual([])
    expect(tableResourceKeysForDomain('identity')).not.toContain('personal-profile')
    expect(tableResourceKeysForDomain('identity')).toContain('work-history')
  })
})
