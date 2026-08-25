import { describe, it, expect } from 'vitest'
import { resolveAgentProfileId } from '@/config/agentProfiles'

describe('resolveAgentProfileId', () => {
  it('routes general chat to the orchestrator even with a page context', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'general',
        pageContext: { route: '/career/vacancies', resource_key: 'vacancies' },
      })
    ).toBe('orchestrator')
  })

  it('locks contextual chat to the section specialist, not another agent', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/career/vacancies', resource_key: 'vacancies' },
      })
    ).toBe('search')
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/pdf-templates' },
      })
    ).toBe('pdf_design')
  })

  it('maps known routes before resource_key', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/linkedin', resource_key: 'linkedin-posts' },
      })
    ).toBe('digital')
  })

  it('maps career resources to their specialist domain', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/career/vacancies', resource_key: 'vacancies' },
      })
    ).toBe('search')
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/career/identity', resource_key: 'identity' },
      })
    ).toBe('identity')
  })

  it('maps PDF admin pages to the pdf_design specialist', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/pdf-templates' },
      })
    ).toBe('pdf_design')
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/pdf-template-styles' },
      })
    ).toBe('pdf_design')
  })

  it('falls back to orchestrator when the page is not mapped', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/dashboard' },
      })
    ).toBe('orchestrator')
  })
})
