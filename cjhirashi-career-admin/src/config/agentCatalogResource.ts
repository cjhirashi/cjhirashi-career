import { ResourceConfig } from '@/config/careerResources'
import { BedrockAgentCatalogItem } from '@/types/bedrock'
import { CareerEntity } from '@/types/career'

const LEVEL_OPTIONS = [
  { value: '1', label: 'L1' },
  { value: '2', label: 'L2' },
  { value: '3', label: 'L3' },
]

const PROMPT_STATUS_OPTIONS = [
  { value: 'default', label: 'Default' },
  { value: 'override', label: 'Override' },
]

const badgeByLevel = (value: unknown) => {
  if (String(value) === '1') return 'cyan' as const
  if (String(value) === '2') return 'success' as const
  return 'slate' as const
}

const badgeByPrompt = (value: unknown) => (value === 'override' ? ('cyan' as const) : ('slate' as const))

/** Same list/vista/edición chrome as a career table, without create/delete. */
export const agentCatalogConfig: ResourceConfig = {
  key: 'settings-agents',
  label: 'Catálogo de Agentes',
  labelSingular: 'agente',
  genderFeminine: false,
  description:
    'Definición en código de cada agente y los overrides editables (prompt, metodologías, secciones, delegación y memoria).',
  columns: [
    { key: 'label', label: 'Agente' },
    { key: 'system_name', label: 'Nombre sistema' },
    { key: 'level', label: 'Nivel', format: 'badge', badgeColor: badgeByLevel },
    { key: 'user_facing', label: 'Chat', format: 'boolean' },
    { key: 'section_count', label: 'Secciones', format: 'number' },
    { key: 'tools_count', label: 'Tools', format: 'number' },
    { key: 'methodology_count', label: 'Metodologías', format: 'number' },
    { key: 'prompt_status', label: 'Prompt', format: 'badge', badgeColor: badgeByPrompt },
    { key: 'memory_label', label: 'Memoria' },
  ],
  fields: [
    { name: 'label', label: 'Agente', type: 'text' },
    { name: 'system_name', label: 'Nombre sistema', type: 'text' },
    { name: 'level', label: 'Nivel', type: 'select', options: LEVEL_OPTIONS },
    { name: 'user_facing', label: 'Chat', type: 'boolean' },
    { name: 'can_delegate', label: 'Delega', type: 'boolean' },
    { name: 'write_enabled', label: 'Escritura', type: 'boolean' },
    { name: 'section_count', label: 'Secciones', type: 'number' },
    { name: 'tools_count', label: 'Tools', type: 'number' },
    { name: 'methodology_count', label: 'Metodologías', type: 'number' },
    { name: 'prompt_status', label: 'Prompt', type: 'select', options: PROMPT_STATUS_OPTIONS },
    { name: 'has_own_memory', label: 'Memoria propia', type: 'boolean' },
    { name: 'memory_label', label: 'Memoria', type: 'text' },
    { name: 'domain_keys', label: 'Dominio', type: 'string-array', fullWidth: true },
  ],
}

export function catalogAgentMatches(
  agent: Pick<BedrockAgentCatalogItem, 'id' | 'profile_id'> & { system_name?: string },
  key: string
): boolean {
  return agent.id === key || agent.profile_id === key || agent.system_name === key
}

export function catalogItemToRow(agent: BedrockAgentCatalogItem): CareerEntity {
  return {
    id: agent.id,
    user_id: '',
    profile_id: agent.profile_id,
    system_name: agent.system_name ?? agent.profile_id,
    label: agent.label,
    level: String(agent.level),
    user_facing: agent.user_facing,
    can_delegate: agent.can_delegate,
    write_enabled: agent.write_enabled,
    section_count: agent.sections?.length ?? 0,
    tools_count: agent.tools.length,
    methodology_count: agent.methodology_count,
    prompt_is_default: agent.prompt_is_default,
    prompt_status: agent.prompt_is_default ? 'default' : 'override',
    has_own_memory: agent.has_own_memory,
    conversation_count: agent.has_own_memory ? agent.conversation_count : null,
    memory_label: agent.has_own_memory ? `${agent.conversation_count} chats` : '—',
    domain_keys: agent.domain_keys,
    photo_url: agent.photo_url ?? null,
  }
}
