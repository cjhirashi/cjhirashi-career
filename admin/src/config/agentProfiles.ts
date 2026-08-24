/**
 * Mirror of `api/src/services/bedrock/agent_profiles.py` — static agent
 * specialist labels for the Admin Panel UI (picker, context chips, delegation
 * status). Keep in sync when profiles are added or renamed on the backend.
 */

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

/** Profiles selectable in contextual chat (orchestrator is auto-routed in general chat). */
export const CONTEXTUAL_AGENT_PROFILES = AGENT_PROFILES.filter((p) => p.id !== 'orchestrator')

const PROFILE_BY_ID = Object.fromEntries(AGENT_PROFILES.map((p) => [p.id, p]))

/** Resolve a profile label by id; falls back to the raw id if unknown. */
export function getAgentProfileLabel(profileId: string): string {
  return PROFILE_BY_ID[profileId]?.label ?? profileId
}
