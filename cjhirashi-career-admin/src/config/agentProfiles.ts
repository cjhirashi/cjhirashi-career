/**
 * Mirror of `api/src/services/bedrock/agent_profiles.py` — static agent
 * specialist labels and routing for the Admin Panel UI (context chips,
 * per-agent session lists). Keep in sync when profiles or route maps change.
 */

import { BedrockChatSurface, BedrockPageContext } from '@/types/bedrock'

export interface AgentProfileOption {
  id: string
  label: string
  level: 1 | 2 | 3
}

export const AGENT_ORCHESTRATOR = 'agent_orchestrator'
export const AGENT_PROFESSIONAL_IDENTITY = 'agent_professional_identity'
export const AGENT_SEARCH_OPERATIONS = 'agent_search_operations'
export const AGENT_DIGITAL_PRESENCE = 'agent_digital_presence'
export const AGENT_NETWORKING = 'agent_networking'
export const AGENT_SUPPORT = 'agent_support'
export const AGENT_METHODOLOGIES = 'agent_methodologies'
export const AGENT_PDF_DESIGN = 'agent_pdf_design'
export const AGENT_PDF_RENDER = 'agent_pdf_render'
export const AGENT_VISUAL_DESIGN = 'agent_visual_design'
export const AGENT_CHANGELOG = 'agent_changelog'
export const AGENT_TASK_MANAGER = 'agent_task_manager'
export const AGENT_LINKEDIN_PUBLISHING = 'agent_linkedin_publishing'
export const AGENT_VACANCY_SEARCH = 'agent_vacancy_search'
export const AGENT_CV_WRITING = 'agent_cv_writing'
export const AGENT_COVER_LETTER_WRITING = 'agent_cover_letter_writing'
export const AGENT_WEB_SEARCH = 'agent_web_search'
export const AGENT_GITHUB = 'agent_github'
export const AGENT_SETTINGS = 'agent_settings'
export const AGENT_CONFIGURATION = 'agent_configuration'

/** User-facing Bedrock agents (L1 + L2). L3 workers are not listed here. */
export const AGENT_PROFILES: AgentProfileOption[] = [
  { id: AGENT_ORCHESTRATOR, label: 'Orquestador', level: 1 },
  { id: AGENT_PROFESSIONAL_IDENTITY, label: 'Identidad Profesional', level: 2 },
  { id: AGENT_SEARCH_OPERATIONS, label: 'Operativa de Búsqueda', level: 2 },
  { id: AGENT_DIGITAL_PRESENCE, label: 'Presencia Digital', level: 2 },
  { id: AGENT_NETWORKING, label: 'Networking', level: 2 },
  { id: AGENT_SUPPORT, label: 'Soporte', level: 2 },
  { id: AGENT_METHODOLOGIES, label: 'Metodologías', level: 2 },
  { id: AGENT_PDF_DESIGN, label: 'Diseño PDF', level: 2 },
  { id: AGENT_CONFIGURATION, label: 'Configuración', level: 2 },
  { id: AGENT_SETTINGS, label: 'Incidencias y Bitácora', level: 2 },
]

/** Catálogo completo (L1/L2/L3) — formularios y labels de delegación. */
export const ALL_AGENT_PROFILES: AgentProfileOption[] = [
  ...AGENT_PROFILES,
  { id: AGENT_PDF_RENDER, label: 'Renderizado PDF', level: 3 },
  { id: AGENT_VISUAL_DESIGN, label: 'Agente Visual', level: 3 },
  { id: AGENT_CHANGELOG, label: 'Gestor de bitácora', level: 3 },
  { id: AGENT_TASK_MANAGER, label: 'Gestor de tareas', level: 3 },
  { id: AGENT_LINKEDIN_PUBLISHING, label: 'Control de publicación LinkedIn', level: 3 },
  { id: AGENT_VACANCY_SEARCH, label: 'Control de búsqueda de vacantes', level: 3 },
  { id: AGENT_CV_WRITING, label: 'Redacción de CVs', level: 3 },
  { id: AGENT_COVER_LETTER_WRITING, label: 'Redacción de cover letters', level: 3 },
  { id: AGENT_WEB_SEARCH, label: 'Consulta web', level: 3 },
  { id: AGENT_GITHUB, label: 'Control GitHub', level: 3 },
]

const AGENT_PROFILE_LABELS: Record<string, string> = Object.fromEntries(
  ALL_AGENT_PROFILES.map((p) => [p.id, p.label])
)

/** Resolve a profile label by id; falls back to the raw id if unknown. */
export function getAgentProfileLabel(profileId: string): string {
  return AGENT_PROFILE_LABELS[profileId] ?? profileId
}

export function allAgentSelectOptions(): { value: string; label: string }[] {
  return ALL_AGENT_PROFILES.map((p) => ({
    value: p.id,
    label: `${p.label} (L${p.level})`,
  }))
}

/**
 * Sólo agentes de nivel 2 — el chat contextual del sidebar derecho de una
 * sección lo atiende un L2 (feature 001). Usado por el selector de agente de
 * la ficha de "Secciones del Admin".
 */
export function l2AgentSelectOptions(): { value: string; label: string }[] {
  return AGENT_PROFILES.filter((p) => p.level === 2).map((p) => ({
    value: p.id,
    label: p.label,
  }))
}

/** Mirror of `_ROUTE_TO_PROFILE` in agent_profiles.py */
const ROUTE_TO_PROFILE: Record<string, string> = {
  '/linkedin': AGENT_DIGITAL_PRESENCE,
  '/job-discovery': AGENT_SEARCH_OPERATIONS,
  '/career/publications': AGENT_DIGITAL_PRESENCE,
  '/career/operational-methodologies': AGENT_METHODOLOGIES,
  '/agent/chat': AGENT_ORCHESTRATOR,
  '/agent/pdf-templates': AGENT_PDF_DESIGN,
  '/agent/pdf-template-styles': AGENT_PDF_DESIGN,
  '/settings/agents': AGENT_CONFIGURATION,
  '/settings/sections': AGENT_CONFIGURATION,
  '/settings/agent-prompts': AGENT_CONFIGURATION,
  '/settings/error-reports': AGENT_SETTINGS,
  '/agent/audit-log': AGENT_SETTINGS,
}

function profileIdForRoute(route: string): string | undefined {
  if (route in ROUTE_TO_PROFILE) return ROUTE_TO_PROFILE[route]
  const matches = Object.entries(ROUTE_TO_PROFILE)
    .filter(([path]) => route.startsWith(`${path}/`))
    .sort((a, b) => b[0].length - a[0].length)
  return matches[0]?.[1]
}

const IDENTITY_RESOURCES = [
  'personal-profile',
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
  'pdf-output-templates': 'document_output',
  'pdf-template-styles': 'document_output',
}

/** Mirror of `_DOMAIN_TO_PROFILE` in agent_profiles.py */
const DOMAIN_TO_PROFILE: Record<string, string> = {
  identity: AGENT_PROFESSIONAL_IDENTITY,
  search: AGENT_SEARCH_OPERATIONS,
  digital: AGENT_DIGITAL_PRESENCE,
  networking: AGENT_NETWORKING,
  support: AGENT_SUPPORT,
  document_output: AGENT_PDF_DESIGN,
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
  if (options.chatSurface === 'general') return AGENT_ORCHESTRATOR
  const page = options.pageContext
  if (page) {
    const route = page.route || ''
    const routeProfile = profileIdForRoute(route)
    if (routeProfile) return routeProfile
    const resourceKey = page.resource_key
    if (resourceKey && resourceKey in RESOURCE_TO_DOMAIN) {
      const domain = RESOURCE_TO_DOMAIN[resourceKey]
      return DOMAIN_TO_PROFILE[domain] ?? AGENT_ORCHESTRATOR
    }
  }
  return AGENT_ORCHESTRATOR
}
