/**
 * Mirror of `api/src/services/bedrock/agent_profiles.py` — static agent
 * specialist labels and routing for the Admin Panel UI (context chips,
 * per-agent session lists). Keep in sync when profiles or route maps change.
 */

import { BedrockChatSurface, BedrockPageContext } from '@/types/bedrock'

export interface AgentProfileOption {
  id: string
  label: string
}

/** All Bedrock agent profiles exposed to the UI (order: orchestrator first). */
export const AGENT_PROFILES: AgentProfileOption[] = [
  { id: 'orchestrator', label: 'Orquestador' },
  { id: 'identity', label: 'Identidad Profesional' },
  { id: 'search', label: 'Operativa de Búsqueda' },
  { id: 'digital', label: 'Presencia Digital' },
  { id: 'networking', label: 'Networking' },
  { id: 'support', label: 'Soporte' },
  { id: 'methodologies', label: 'Metodologías' },
  { id: 'pdf_design', label: 'Diseño PDF' },
  { id: 'visual_design', label: 'Agente Visual' },
]

const PROFILE_BY_ID = Object.fromEntries(AGENT_PROFILES.map((p) => [p.id, p]))

/** Resolve a profile label by id; falls back to the raw id if unknown. */
export function getAgentProfileLabel(profileId: string): string {
  return PROFILE_BY_ID[profileId]?.label ?? profileId
}

/** Mirror of `_ROUTE_TO_PROFILE` in agent_profiles.py */
const ROUTE_TO_PROFILE: Record<string, string> = {
  '/linkedin': 'digital',
  '/job-discovery': 'search',
  '/career/publications': 'digital',
  '/career/operational-methodologies': 'methodologies',
  '/agent/chat': 'orchestrator',
  '/agent/pdf-templates': 'pdf_design',
  '/agent/pdf-template-styles': 'pdf_design',
}

const IDENTITY_RESOURCES = [
  'differentiators',
  'identity',
  'identity-reflections',
  'competencies',
  'certifications',
  'target-roles',
  'work-history',
  'achievements',
  'star-stories',
  'career-reviews',
  'role-gap-analysis',
  'projects',
]

const SEARCH_RESOURCES = [
  'fit-scoring-factors',
  'market-segments',
  'role-narratives',
  'search-plans',
  'networking-contacts',
  'target-companies',
  'vacancies',
  'cv-versions',
  'cover-letter-versions',
  'applications',
  'application-interactions',
  'interviews',
]

const DIGITAL_RESOURCES = [
  'linkedin-profile',
  'github-profile',
  'portal-home',
  'portal-about',
  'portal-contact',
  'publications',
]

/** Mirror of `_RESOURCE_TO_DOMAIN` in agent_profiles.py */
const RESOURCE_TO_DOMAIN: Record<string, string> = {
  ...Object.fromEntries(IDENTITY_RESOURCES.map((k) => [k, 'identity'])),
  ...Object.fromEntries(SEARCH_RESOURCES.map((k) => [k, 'search'])),
  ...Object.fromEntries(DIGITAL_RESOURCES.map((k) => [k, 'digital'])),
  'contact-interactions': 'networking',
  'networking-activities': 'networking',
  tags: 'support',
  'operational-methodologies': 'methodologies',
}

/** Mirror of `_DOMAIN_TO_PROFILE` in agent_profiles.py */
const DOMAIN_TO_PROFILE: Record<string, string> = {
  identity: 'identity',
  search: 'search',
  digital: 'digital',
  networking: 'networking',
  support: 'support',
}

/**
 * Same routing as `resolve_agent_profile` on the API: general → orchestrator;
 * contextual → specialist of the current section (route, then resource_key).
 * There is no manual override: a section always talks to its own specialist.
 */
export function resolveAgentProfileId(options: {
  chatSurface: BedrockChatSurface
  pageContext?: BedrockPageContext | null
}): string {
  if (options.chatSurface === 'general') return 'orchestrator'
  const page = options.pageContext
  if (page) {
    const route = page.route || ''
    if (route in ROUTE_TO_PROFILE) return ROUTE_TO_PROFILE[route]
    const resourceKey = page.resource_key
    if (resourceKey && resourceKey in RESOURCE_TO_DOMAIN) {
      const domain = RESOURCE_TO_DOMAIN[resourceKey]
      return DOMAIN_TO_PROFILE[domain] ?? 'orchestrator'
    }
  }
  return 'orchestrator'
}
