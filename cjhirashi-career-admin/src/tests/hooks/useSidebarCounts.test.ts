import { describe, it, expect } from 'vitest'
import { isTableResource, CAREER_RESOURCES } from '@/config/careerResources'
import { tableResourceKeysForGroup } from '@/hooks/useSidebarCounts'
import { NavGroup } from '@/types/adminSections'

const emptyView = {
  id: 'vw-1',
  key: 'main',
  label: 'Principal',
  sort_order: 0,
  data_source: 'crud' as const,
  resource_key: null,
  has_controls_window: false,
  tool_names: [],
  responsible_agent_profile_id: null,
  has_instructions: false,
  chat_enabled: false,
}

const section = (systemName: string, sortOrder: number) => ({
  id: `s1-${sortOrder}`,
  level: 1 as const,
  system_name: systemName,
  label: systemName,
  path: `/career/${systemName.replace(/^career-/, '')}`,
  section_type: 'table',
  sort_order: sortOrder,
  origin: 'code',
  has_layout: true,
  view_count: 1,
  views: [emptyView],
  children: [],
})

const sampleGroups: NavGroup[] = [
  {
    id: 'grp-9',
    system_name: 'professional-identity',
    name: 'Identidad Profesional',
    sort_order: 100,
    sections: [
      section('career-personal-profile', 100),
      section('career-work-history', 107),
    ],
  },
  {
    id: 'grp-4',
    system_name: 'digital-presence',
    name: 'Presencia Digital',
    sort_order: 30,
    sections: [
      { ...section('linkedin-publish', 30), path: '/linkedin' },
      section('career-publications', 145),
    ],
  },
  {
    id: 'grp-11',
    system_name: 'support',
    name: 'Soporte',
    sort_order: 160,
    sections: [section('career-tags', 160)],
  },
]

describe('sidebar table resources', () => {
  it('treats list resources as tables and singletons as not', () => {
    expect(isTableResource(CAREER_RESOURCES['work-history'])).toBe(true)
    expect(isTableResource(CAREER_RESOURCES['personal-profile'])).toBe(false)
    expect(isTableResource(CAREER_RESOURCES.identity)).toBe(false)
    expect(isTableResource(undefined)).toBe(false)
  })

  it('returns only table keys for a group, in section order', () => {
    expect(tableResourceKeysForGroup('digital-presence', sampleGroups)).toEqual(['publications'])
    expect(tableResourceKeysForGroup('support', sampleGroups)).toEqual(['tags'])
    expect(tableResourceKeysForGroup(null, sampleGroups)).toEqual([])
    expect(tableResourceKeysForGroup('professional-identity', undefined)).toEqual([])
    expect(tableResourceKeysForGroup('professional-identity', sampleGroups)).not.toContain(
      'personal-profile'
    )
    expect(tableResourceKeysForGroup('professional-identity', sampleGroups)).toContain('work-history')
  })

  it('ignores non-career sections (they are not table resources by resourceKey)', () => {
    expect(tableResourceKeysForGroup('digital-presence', sampleGroups)).not.toContain('linkedin-publish')
  })
})
