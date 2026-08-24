/**
 * Mirror of `api/src/services/bedrock/section_profiles.py` — maps routes and
 * career resources to a recommended Bedrock model id for contextual chat.
 * Keep in sync with the backend when profiles or model ids change.
 */

import { BedrockPageContext } from '@/types/bedrock'

/** Named chat profiles → AWS Bedrock model id. */
export const CHAT_PROFILE_MODELS: Record<string, string> = {
  crud_standard: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
  strategy: 'deepseek.v3.2',
  narrative: 'us.anthropic.claude-sonnet-4-5-20250929-v1:0',
  digital_presence: 'us.anthropic.claude-sonnet-4-5-20250929-v1:0',
  methodology: 'cohere.command-r-v1:0',
  read_light: 'amazon.nova-lite-v1:0',
  agent_admin: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
  singleton_identity: 'mistral.mistral-large-2402-v1:0',
}

/** Human-readable labels for chat profiles (shown in context chips). */
export const CHAT_PROFILE_LABELS: Record<string, string> = {
  crud_standard: 'CRUD estándar',
  strategy: 'Estrategia',
  narrative: 'Narrativa',
  digital_presence: 'Presencia digital',
  methodology: 'Metodología',
  read_light: 'Lectura ligera',
  agent_admin: 'Admin agente',
  singleton_identity: 'Identidad (singleton)',
}

const RESOURCE_CHAT_PROFILE: Record<string, string> = {
  vacancies: 'strategy',
  'search-plans': 'strategy',
  'fit-scoring-factors': 'strategy',
  'target-companies': 'strategy',
  'target-roles': 'strategy',
  applications: 'strategy',
  'cv-versions': 'narrative',
  'cover-letter-versions': 'narrative',
  'role-narratives': 'narrative',
  'star-stories': 'narrative',
  'identity-reflections': 'narrative',
  publications: 'digital_presence',
  'linkedin-profile': 'digital_presence',
  'operational-methodologies': 'methodology',
  identity: 'singleton_identity',
}

const STATIC_ROUTE_PROFILE: Record<string, string> = {
  '/dashboard': 'read_light',
  '/metrics': 'read_light',
  '/search-metrics': 'read_light',
  '/job-discovery': 'strategy',
  '/files': 'agent_admin',
  '/linkedin': 'digital_presence',
  '/agent/chat': 'read_light',
}

/**
 * Resolve the chat profile key for a page context (without looking up the model id).
 * Used to populate `page_context.chat_profile` for the harness.
 */
export function resolveChatProfileKey(pageContext: BedrockPageContext | null | undefined): string | null {
  if (!pageContext) return null
  const route = pageContext.route ?? ''
  if (route in STATIC_ROUTE_PROFILE) return STATIC_ROUTE_PROFILE[route]
  if (pageContext.chat_profile && pageContext.chat_profile in CHAT_PROFILE_MODELS) {
    return pageContext.chat_profile
  }
  const rk = pageContext.resource_key
  if (rk && rk in RESOURCE_CHAT_PROFILE) return RESOURCE_CHAT_PROFILE[rk]
  return 'crud_standard'
}

/**
 * Recommended model id for contextual chat given page context.
 * Falls back to `crud_standard` model when no mapping matches.
 */
export function resolveRecommendedModel(
  pageContext: BedrockPageContext | null | undefined,
  fallbackModelId?: string
): string {
  const key = resolveChatProfileKey(pageContext)
  if (key && key in CHAT_PROFILE_MODELS) return CHAT_PROFILE_MODELS[key]
  return fallbackModelId ?? CHAT_PROFILE_MODELS.crud_standard
}
