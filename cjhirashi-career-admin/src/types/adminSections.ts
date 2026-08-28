/**
 * Jerarquía de secciones del Admin + vistas (ADR-023). Reemplaza el contrato
 * plano `sec-N` de ADR-021/022 (ver `023-admin-sections-hierarchy-views.md`).
 * Mirror de `api/src/schemas/admin_sections.py`.
 */

export type AdminSectionType = 'table' | 'functional' | 'metrics' | 'bucket'

export const ADMIN_SECTION_TYPE_LABEL: Record<string, string> = {
  table: 'tabla',
  functional: 'funcional',
  metrics: 'métricas',
  bucket: 'bucket',
}

export type AdminDataSource = 'crud' | 'computed' | 'singleton' | 'external'

export const ADMIN_DATA_SOURCE_LABEL: Record<string, string> = {
  crud: 'CRUD',
  computed: 'Calculada',
  singleton: 'Singleton',
  external: 'Externa',
}

// ---------------------------------------------------------------------------
// nav-tree (GET /admin/nav-tree)
// ---------------------------------------------------------------------------

export interface NavView {
  id: string
  key: string
  label: string
  sort_order: number
  data_source: AdminDataSource | string
  resource_key: string | null
  has_controls_window: boolean
  tool_names: string[]
  responsible_agent_profile_id: string | null
  has_instructions: boolean
  chat_enabled: boolean
}

export interface NavSection {
  id: string
  level: 1 | 2 | 3
  system_name: string
  label: string
  path: string | null
  section_type: AdminSectionType | string
  sort_order: number
  origin: string
  has_layout: boolean
  view_count: number
  views: NavView[]
  children: NavSection[]
}

export interface NavGroup {
  id: string
  system_name: string
  name: string
  sort_order: number
  sections: NavSection[]
}

export interface NavTreeResponse {
  groups: NavGroup[]
  generated_at: string
}

// ---------------------------------------------------------------------------
// Grupos (GET/PUT /admin/section-groups)
// ---------------------------------------------------------------------------

export interface SectionGroupItem {
  id: string
  system_name: string
  name: string
  sort_order: number
}

// ---------------------------------------------------------------------------
// Secciones (GET/PUT /admin/sections/*)
// ---------------------------------------------------------------------------

export interface SectionListItem {
  id: string
  level: 1 | 2 | 3
  system_name: string
  label: string
  path: string | null
  section_type: AdminSectionType | string
  sort_order: number
  origin: string
  group_id: string | null
  parent_id: string | null
  view_count: number
}

export interface SectionDetail extends SectionListItem {
  views: NavView[]
}

export interface SectionReparentRequest {
  sort_order?: number
  /** Solo L1: mover a otro grupo. */
  group_id?: string
  /** Solo L2/L3: mover a otro padre del mismo nivel. */
  parent_id?: string
}

export interface SectionReorderRequest {
  container_id: string
  order: string[]
}

// ---------------------------------------------------------------------------
// Vistas (GET/PUT /admin/views/*)
// ---------------------------------------------------------------------------

export interface AdminViewOwner {
  level: 1 | 2 | 3
  section_id: string
  section_system_name: string
  section_label: string
  section_path: string | null
}

export interface AdminViewItem {
  id: string
  owner: AdminViewOwner
  key: string
  label: string
  sort_order: number
  data_source: AdminDataSource | string
  resource_key: string | null
  has_controls_window: boolean
  tool_names: string[]
  responsible_agent_profile_id: string | null
  responsible_agent_label: string | null
  responsible_is_l2: boolean
  instructions: string | null
  chat_enabled: boolean
  instructions_enabled: boolean
}

export interface AdminViewUpdateRequest {
  /** System name de un perfil L2. "" quita el responsable. Omitir = sin cambio. */
  responsible_agent_profile_id?: string
  /** Texto del panel del sidebar. "" borra el panel. Omitir = sin cambio. */
  instructions?: string
}

// ---------------------------------------------------------------------------
// Helpers de matching (sidebar derecho / chat contextual)
// ---------------------------------------------------------------------------

/** Flattened view row with a resolved absolute-ish path, used for route matching. */
export interface FlatNavSection {
  id: string
  level: 1 | 2 | 3
  system_name: string
  label: string
  path: string | null
  views: NavView[]
}

function flattenSections(sections: NavSection[], acc: FlatNavSection[] = []): FlatNavSection[] {
  for (const section of sections) {
    acc.push({
      id: section.id,
      level: section.level,
      system_name: section.system_name,
      label: section.label,
      path: section.path,
      views: section.views,
    })
    if (section.children.length) flattenSections(section.children, acc)
  }
  return acc
}

export function flattenNavTree(tree: NavTreeResponse | undefined): FlatNavSection[] {
  if (!tree) return []
  return tree.groups.flatMap((group) => flattenSections(group.sections))
}

/**
 * Route -> (section, active view) match, mirroring the backend's
 * `match_active_view` (exact path, then longest-prefix). Used by the right
 * sidebar (instructions panel) and the contextual chat profile resolution.
 */
export function matchActiveView(
  pathname: string,
  sections: FlatNavSection[],
  viewKey?: string | null
): { section: FlatNavSection; view: NavView } | null {
  const path = pathname.replace(/\/+$/, '') || '/'
  const withPath = sections.filter((section): section is FlatNavSection & { path: string } =>
    Boolean(section.path)
  )
  const exact = withPath.find((section) => section.path === path)
  const prefixed = withPath
    .filter((section) => path.startsWith(`${section.path}/`))
    .sort((a, b) => b.path.length - a.path.length)
  const section = exact ?? prefixed[0]
  if (!section || section.views.length === 0) return null

  if (viewKey) {
    const byKey = section.views.find((view) => view.key === viewKey)
    if (byKey) return { section, view: byKey }
  }
  if (!exact) {
    const record =
      section.views.find((view) => view.key === 'view') ??
      section.views.find((view) => view.key === 'record')
    if (record) return { section, view: record }
  }
  const sorted = [...section.views].sort((a, b) => a.sort_order - b.sort_order)
  return { section, view: sorted[0] }
}
