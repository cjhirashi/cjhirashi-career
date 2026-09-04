import { describe, it, expect } from 'vitest'
import {
  AGENT_CHANGELOG,
  AGENT_DIGITAL_PRESENCE,
  AGENT_LINKEDIN_PUBLISHING,
  AGENT_ORCHESTRATOR,
  AGENT_PDF_DESIGN,
  AGENT_PDF_RENDER,
  AGENT_PROFILES,
  ALL_AGENT_PROFILES,
  AGENT_PROFESSIONAL_IDENTITY,
  AGENT_SEARCH_OPERATIONS,
  AGENT_VACANCY_SEARCH,
  AGENT_CV_WRITING,
  AGENT_COVER_LETTER_WRITING,
  AGENT_VISUAL_DESIGN,
  AGENT_WEB_SEARCH,
  AGENT_GITHUB,
  AGENT_SETTINGS,
  AGENT_CONFIGURATION,
  allAgentSelectOptions,
  getAgentProfileLabel,
  l2AgentSelectOptions,
  resolveAgentProfileId,
} from '@/config/agentProfiles'

describe('resolveAgentProfileId', () => {
  it('routes general chat to the orchestrator even with a page context', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'general',
        pageContext: { route: '/career/vacancies', resource_key: 'vacancies' },
      })
    ).toBe(AGENT_ORCHESTRATOR)
  })

  it('locks contextual chat to the section specialist, not another agent', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/career/vacancies', resource_key: 'vacancies' },
      })
    ).toBe(AGENT_SEARCH_OPERATIONS)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/pdf-templates' },
      })
    ).toBe(AGENT_PDF_DESIGN)
  })

  it('maps known routes before resource_key', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/linkedin', resource_key: 'linkedin-posts' },
      })
    ).toBe(AGENT_DIGITAL_PRESENCE)
  })

  it('maps career resources to their specialist domain', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/career/vacancies', resource_key: 'vacancies' },
      })
    ).toBe(AGENT_SEARCH_OPERATIONS)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/career/identity', resource_key: 'identity' },
      })
    ).toBe(AGENT_PROFESSIONAL_IDENTITY)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/career/personal-profile', resource_key: 'personal-profile' },
      })
    ).toBe(AGENT_PROFESSIONAL_IDENTITY)
  })

  it('maps PDF admin pages to the agent_pdf_design specialist', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/pdf-templates' },
      })
    ).toBe(AGENT_PDF_DESIGN)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/pdf-templates/cv-ats-optimizado' },
      })
    ).toBe(AGENT_PDF_DESIGN)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/pdf-template-styles/pds-cyan' },
      })
    ).toBe(AGENT_PDF_DESIGN)
  })

  it('maps the configuration Settings pages to agent_configuration (ADR-022)', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/settings/agents' },
      })
    ).toBe(AGENT_CONFIGURATION)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/settings/agents/agent-2' },
      })
    ).toBe(AGENT_CONFIGURATION)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/settings/sections' },
      })
    ).toBe(AGENT_CONFIGURATION)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/settings/agent-prompts' },
      })
    ).toBe(AGENT_CONFIGURATION)
  })

  it('maps incidents/audit-log pages to agent_settings (ADR-022)', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/settings/error-reports' },
      })
    ).toBe(AGENT_SETTINGS)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/audit-log' },
      })
    ).toBe(AGENT_SETTINGS)
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/agent/audit-log/err-3' },
      })
    ).toBe(AGENT_SETTINGS)
  })

  it('exposes both metaconfig L2 profiles with distinct labels (ADR-022)', () => {
    const ids = AGENT_PROFILES.map((p) => p.id)
    expect(ids).toContain(AGENT_CONFIGURATION)
    expect(ids).toContain(AGENT_SETTINGS)
    expect(getAgentProfileLabel(AGENT_CONFIGURATION)).toBe('Configuración')
    expect(getAgentProfileLabel(AGENT_SETTINGS)).toBe('Incidencias y Bitácora')
    expect(AGENT_PROFILES.find((p) => p.id === AGENT_CONFIGURATION)?.level).toBe(2)
    expect(AGENT_PROFILES.find((p) => p.id === AGENT_SETTINGS)?.level).toBe(2)
  })

  it('falls back to orchestrator when the page is not mapped', () => {
    expect(
      resolveAgentProfileId({
        chatSurface: 'contextual',
        pageContext: { route: '/dashboard' },
      })
    ).toBe(AGENT_ORCHESTRATOR)
  })

  it('does not expose L3 workers as user-facing profiles', () => {
    const ids = AGENT_PROFILES.map((p) => p.id)
    expect(ids).not.toContain(AGENT_PDF_RENDER)
    expect(ids).not.toContain(AGENT_VISUAL_DESIGN)
    expect(ids).not.toContain(AGENT_CHANGELOG)
    expect(ids).not.toContain(AGENT_LINKEDIN_PUBLISHING)
    expect(ids).not.toContain(AGENT_VACANCY_SEARCH)
    expect(ids).not.toContain(AGENT_CV_WRITING)
    expect(ids).not.toContain(AGENT_COVER_LETTER_WRITING)
    expect(ids).not.toContain(AGENT_WEB_SEARCH)
    expect(ids).not.toContain(AGENT_GITHUB)
    expect(getAgentProfileLabel(AGENT_PDF_RENDER)).toBe('Renderizado PDF')
    expect(getAgentProfileLabel(AGENT_LINKEDIN_PUBLISHING)).toBe('Control de publicación LinkedIn')
    expect(getAgentProfileLabel(AGENT_VACANCY_SEARCH)).toBe('Control de búsqueda de vacantes')
    expect(getAgentProfileLabel(AGENT_CV_WRITING)).toBe('Redacción de CVs')
    expect(getAgentProfileLabel(AGENT_COVER_LETTER_WRITING)).toBe('Redacción de cover letters')
    expect(getAgentProfileLabel(AGENT_WEB_SEARCH)).toBe('Consulta web')
    expect(getAgentProfileLabel(AGENT_GITHUB)).toBe('Control GitHub')
  })

  it('lists L3 agents in ALL_AGENT_PROFILES for methodology targeting', () => {
    const ids = ALL_AGENT_PROFILES.map((p) => p.id)
    expect(ids).toContain(AGENT_PDF_RENDER)
    expect(ids).toContain(AGENT_GITHUB)
    expect(allAgentSelectOptions().some((o) => o.value === AGENT_PDF_DESIGN)).toBe(true)
    expect(AGENT_PROFILES.every((p) => p.level !== 3)).toBe(true)
  })

  it('l2AgentSelectOptions lists only L2 agents (RF-014)', () => {
    const opts = l2AgentSelectOptions()
    const values = opts.map((o) => o.value)
    expect(values).toContain(AGENT_CONFIGURATION)
    expect(values).toContain(AGENT_PDF_DESIGN)
    expect(values).not.toContain(AGENT_ORCHESTRATOR) // L1
    expect(values).not.toContain(AGENT_VACANCY_SEARCH) // L3
    expect(values).not.toContain(AGENT_CHANGELOG) // L3
    expect(opts).toHaveLength(AGENT_PROFILES.filter((p) => p.level === 2).length)
  })
})
