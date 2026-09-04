export type AdminSectionType = 'table' | 'functional' | 'metrics' | 'bucket'

export const ADMIN_SECTION_TYPE_LABEL: Record<string, string> = {
  table: 'tabla',
  functional: 'funcional',
  metrics: 'métricas',
  bucket: 'bucket',
}

export interface AdminSectionView {
  key: string
  label: string
  description: string
  sidebar_title: string
  /** Instrucciones del sidebar derecho (Markdown/GFM). '' = override vacío explícito. */
  sidebar_body: string
  is_default: boolean
}

export interface AdminSection {
  id: string
  system_name: string
  label: string
  path: string
  section_type: AdminSectionType | string
  group: string
  resource_key: string | null
  related_tools: string[]
  default_agent_profile_id: string | null
  /** Agente L2 del chat contextual del sidebar derecho, o null = sin chat. */
  agent_profile_id: string | null
  agent_label: string | null
  agent_is_default: boolean
  sidebar_has_chat: boolean
  sidebar_has_instructions: boolean
  view_count: number
  views: AdminSectionView[]
}

export interface AdminSectionUpdate {
  agent_profile_id?: string | null
  views?: Record<string, Partial<Pick<AdminSectionView, 'description' | 'sidebar_title' | 'sidebar_body'>>>
}

export function matchAdminSection(
  pathname: string,
  sections: AdminSection[]
): { section: AdminSection; view: AdminSectionView } | null {
  const path = pathname.replace(/\/+$/, '') || '/'
  const exact = sections.find((section) => section.path === path)
  if (exact) {
    return { section: exact, view: exact.views[0] }
  }
  const prefixed = sections
    .filter((section) => path.startsWith(`${section.path}/`))
    .sort((a, b) => b.path.length - a.path.length)
  const section = prefixed[0]
  if (!section) return null
  const record = section.views.find((view) => view.key === 'view')
    ?? section.views.find((view) => view.key === 'record')
  return { section, view: record ?? section.views[section.views.length - 1] }
}
