// ============================================================================
// Declarative configuration for every career-domain (v2) resource.
//
// This is the frontend mirror of the backend's generic CRUD router factory
// (api/src/routes/career_common.py): instead of 24 near-identical page
// components, each resource is described as data (endpoint, table columns,
// form fields) and rendered by the single generic `CareerResourceView`
// component (see src/components/career/CareerResourceView.tsx).
// ============================================================================

import {
  Activity,
  Award,
  BookOpen,
  Bookmark,
  Briefcase,
  Building2,
  Calendar,
  Circle,
  ClipboardCheck,
  Compass,
  FileText,
  Folder,
  GitBranch,
  Github,
  Globe,
  GraduationCap,
  Handshake,
  Home,
  Layers,
  Lightbulb,
  Linkedin,
  Mail,
  Map,
  MessageSquare,
  MessagesSquare,
  Newspaper,
  PieChart,
  Quote,
  Scale,
  Search,
  Send,
  Sparkles,
  Star,
  Tag,
  Target,
  Trophy,
  User,
  UserCircle,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { allAgentSelectOptions } from '@/config/agentProfiles'

export type FieldType =
  | 'text'
  | 'textarea'
  | 'code'
  | 'number'
  | 'date'
  | 'datetime'
  | 'boolean'
  | 'select'
  | 'creatable-select' // distinct values of this column; typing a new one grows the list
  | 'multi-select'
  | 'string-array' // newline-separated list -> string[]
  | 'number-array' // comma-separated list -> number[]
  | 'json' // list of records (kv / text / objects) stored as JSONB
  | 'fk-select' // FK selector: fetches options from another career resource
  | 'fk-multi-select' // several FKs: themed dropdown multi-select from another career resource

export interface SelectOption {
  value: string
  label: string
  /** When set (including null), the select shows a photo/initials instead of the id rail. */
  imageUrl?: string | null
}

/** One input inside a json-list record (kind: 'records'). */
export interface JsonListItemField {
  name: string
  label: string
  type?: 'text' | 'textarea' | 'date' | 'url'
  placeholder?: string
  /** Span the full row in the record grid. */
  wide?: boolean
}

/**
 * How a JSONB field is edited and shown: never as raw JSON.
 * - `kv`: list of name + value (metrics, context).
 * - `text`: list of single-line items (sources, results).
 * - `records`: list of objects with `itemFields`.
 */
export interface JsonListConfig {
  kind: 'kv' | 'text' | 'records'
  /** Singular noun for counts and empty copy: "métrica", "experiencia". */
  itemNoun: string
  addLabel?: string
  keyLabel?: string
  valueLabel?: string
  keyPlaceholder?: string
  valuePlaceholder?: string
  textPlaceholder?: string
  itemFields?: JsonListItemField[]
}

export interface FieldConfig {
  name: string
  label: string
  type: FieldType
  required?: boolean
  options?: SelectOption[]
  placeholder?: string
  helpText?: string
  /** Render this field spanning both columns of the two-column form grid. */
  fullWidth?: boolean
  /**
   * For type='fk-select' or 'fk-multi-select': the career resource key to fetch
   * options from. E.g. 'target-roles', 'competencies', 'vacancies'.
   */
  fkResource?: string
  /**
   * For type='fk-select' or 'fk-multi-select': the field(s) on the referenced
   * record to use as display label. First non-empty value wins.
   * Defaults to ['name','title'].
   */
  fkLabelField?: string | string[]
  /** For type='fk-select' or 'fk-multi-select': API source when not under /career/{key}. */
  fkApi?: 'career' | 'pdf-template-styles'
  /**
   * For type='fk-multi-select': lets Carlos type a value not yet in
   * `fkResource`'s options - it is sent as-is and the backend creates the
   * referenced record (see projects.competency_ids / CareerRepository).
   */
  creatable?: boolean
  /** For type='json': list editor instead of a JSON textarea. */
  jsonList?: JsonListConfig
}

export type ColumnFormat = 'text' | 'date' | 'datetime' | 'boolean' | 'badge' | 'truncate' | 'number' | 'agents'

export interface ColumnConfig {
  key: string
  label: string
  format?: ColumnFormat
  /** Maps a raw value to a badge color when format === 'badge'. */
  badgeColor?: (value: unknown) => 'cyan' | 'slate' | 'success' | 'error' | 'warning'
}

export interface ResourceConfig {
  /** kebab-case key, matches the API path segment under /career/{key}. */
  key: string
  label: string
  labelSingular: string
  /** Spanish grammatical gender of `labelSingular`, for "Nuevo/Nueva" and
   * "este/esta" agreement in the UI (ResourceForm/CareerResourceView). */
  genderFeminine: boolean
  description?: string
  /** `singleton`: the table has (at most) one row per user (e.g. `identity`). */
  mode?: 'list' | 'singleton'
  columns: ColumnConfig[]
  fields: FieldConfig[]
  /** Marks this resource as PDF-exportable: the named field (its Markdown
   * "content") is hidden from the plain INFORMACIÓN field list in the
   * record viewer and replaced there by an embedded, auto-loaded preview of
   * the actual generated PDF instead - see CareerResourceView's
   * `pdfExportField` handling. Requires a real `POST /career/{key}/{id}/pdf`
   * endpoint on the backend (see `careerApi.generateResourcePdf`), unless
   * `pdfPreviewSource` is `template-render`. */
  pdfExportField?: string
  /** How to fetch the embedded PDF preview in record view. Defaults to
   * `career-pdf` (`POST /career/{key}/{id}/pdf`). Use `template-render` for
   * HTML/CSS templates rendered via `POST /pdf-templates/{id}/render`. */
  pdfPreviewSource?: 'career-pdf' | 'template-render'
  /** Extra fields hidden from record view when a PDF preview is shown
   * (defaults to `[pdfExportField]` when that is set). */
  pdfPreviewHiddenFields?: string[]
}

const badgeByEvaluation = (value: unknown) => {
  if (value === 'apply') return 'success' as const
  if (value === 'do_not_apply') return 'error' as const
  return 'warning' as const
}

const badgeByStatusGeneric = (value: unknown) => {
  const v = String(value)
  if (['active', 'approved', 'final', 'published', 'converted', 'completed', 'apply', 'offer'].includes(v))
    return 'success' as const
  if (['archived', 'rejected', 'do_not_apply', 'cancelled', 'paused'].includes(v)) return 'error' as const
  if (['draft', 'pending', 'pending_review', 'not_started', 'in_progress', 'scheduled'].includes(v))
    return 'warning' as const
  return 'slate' as const
}

const fitBadge = (value: unknown) => {
  const n = Number(value)
  if (Number.isNaN(n)) return 'slate' as const
  if (n >= 80) return 'success' as const
  if (n >= 50) return 'warning' as const
  return 'error' as const
}

// ---------------------------------------------------------------------------
// Dominio 1: Identidad Profesional
// ---------------------------------------------------------------------------

export const personalProfileConfig: ResourceConfig = {
  key: 'personal-profile',
  label: 'Datos personales',
  labelSingular: 'Ficha personal',
  genderFeminine: true,
  mode: 'singleton',
  description:
    'Ficha biográfica de referencia para el gestor de carrera y los agentes: nombre legal, fecha de nacimiento, ubicación, contacto e idiomas. No es la narrativa profesional (eso vive en Identidad). Úsala como fuente de verdad al redactar CVs, cartas y formularios.',
  columns: [],
  fields: [
    { name: 'full_name', label: 'Nombre completo', type: 'text', required: true, fullWidth: true },
    { name: 'preferred_name', label: 'Nombre preferido', type: 'text', helpText: 'Cómo quieres que te llamen o cómo aparece el nombre corto en un CV.' },
    { name: 'date_of_birth', label: 'Fecha de nacimiento', type: 'date' },
    { name: 'nationality', label: 'Nacionalidad', type: 'text' },
    { name: 'city', label: 'Ciudad', type: 'text' },
    { name: 'country', label: 'País', type: 'text' },
    { name: 'phone', label: 'Teléfono', type: 'text' },
    { name: 'email', label: 'Correo de contacto', type: 'text', helpText: 'Correo que debe ir en CVs y postulaciones; no tiene que ser el del login.' },
    {
      name: 'languages',
      label: 'Idiomas',
      type: 'textarea',
      fullWidth: true,
      helpText: 'Markdown. Ej. Español nativo, Inglés C1.',
    },
    {
      name: 'work_authorization',
      label: 'Autorización de trabajo',
      type: 'textarea',
      fullWidth: true,
      helpText: 'Visas, ciudadanía, restricciones geográficas relevantes para postulaciones.',
    },
    {
      name: 'notes',
      label: 'Notas personales',
      type: 'textarea',
      fullWidth: true,
      helpText: 'Contexto extra para el gestor de carrera (familia, movilidad, disponibilidad, etc.).',
    },
  ],
}

export const differentiatorsConfig: ResourceConfig = {
  key: 'differentiators',
  label: 'Diferenciadores',
  labelSingular: 'Diferenciador',
  genderFeminine: false,
  description:
    'Tus pilares de ventaja competitiva verificable (5-7 activos máximo) - nunca adjetivos sueltos, cada uno necesita evidencia real en "Evidencia" para pasar a tu narrativa comunicable. Es la raíz de la que se derivan tus roles objetivo.',
  columns: [
    { key: 'pillar_name', label: 'Pilar' },
    { key: 'is_active', label: 'Activo', format: 'boolean' },
  ],
  fields: [
    { name: 'pillar_name', label: 'Nombre del pilar', type: 'text', required: true },
    { name: 'pillar_description', label: 'Descripción', type: 'textarea', fullWidth: true },
    { name: 'strengths', label: 'Fortalezas', type: 'textarea', fullWidth: true },
    { name: 'evidence', label: 'Evidencia', type: 'textarea', fullWidth: true },
    { name: 'is_active', label: 'Activo', type: 'boolean' },
  ],
}

export const identityConfig: ResourceConfig = {
  key: 'identity',
  label: 'Identidad',
  labelSingular: 'Identidad',
  genderFeminine: true,
  mode: 'singleton',
  description:
    'Tu narrativa comunicable: tagline, bio y propuesta de valor. Se redacta al final, como resultado de Reflexiones IKIGAI, Diferenciadores y Roles Objetivo - nunca al revés. También es la base del elevator pitch hablado, que no se guarda en ningún campo.',
  columns: [],
  fields: [
    { name: 'professional_tagline', label: 'Tagline profesional', type: 'text', fullWidth: true },
    { name: 'bio_summary', label: 'Bio resumen', type: 'textarea', fullWidth: true },
    {
      name: 'unique_value_proposition',
      label: 'Propuesta de valor única',
      type: 'textarea',
      fullWidth: true,
    },
  ],
}

export const identityReflectionsConfig: ResourceConfig = {
  key: 'identity-reflections',
  label: 'Reflexiones IKIGAI',
  labelSingular: 'Reflexión',
  genderFeminine: true,
  description:
    'Una reflexión honesta por cada una de las 4 dimensiones IKIGAI (lo que amas, sabes, el mundo necesita, paga), con evidencia concreta. Es la raíz de todo el dominio de Identidad: sin las 4 alineadas hay riesgo de burnout, insatisfacción, superfluidad o expertise insuficiente.',
  columns: [
    { key: 'dimension', label: 'Dimensión', format: 'badge' },
    { key: 'content', label: 'Contenido', format: 'truncate' },
  ],
  fields: [
    {
      name: 'dimension',
      label: 'Dimensión',
      type: 'select',
      required: true,
      options: [
        { value: 'passion', label: 'Pasión' },
        { value: 'profession', label: 'Profesión' },
        { value: 'vocation', label: 'Vocación' },
        { value: 'mission', label: 'Misión' },
      ],
    },
    { name: 'content', label: 'Contenido', type: 'textarea', fullWidth: true },
    { name: 'tags', label: 'Tags', type: 'textarea', fullWidth: true },
  ],
}

export const competenciesConfig: ResourceConfig = {
  key: 'competencies',
  label: 'Competencias',
  labelSingular: 'Competencia',
  genderFeminine: true,
  description:
    'Tu inventario de habilidades técnicas, transferibles y de negocio, siempre respaldado por evidencia real en "Descripción de profundidad" - nunca aspiracional. Marca "Destacado en home" para decidir qué categorías aparecen como badge en el Home público.',
  columns: [
    { key: 'name', label: 'Nombre' },
    { key: 'type', label: 'Tipo', format: 'badge' },
    { key: 'category', label: 'Categoría' },
    { key: 'level', label: 'Nivel' },
    { key: 'years_of_experience', label: 'Años exp.', format: 'number' },
    { key: 'proficiency_score', label: 'Score', format: 'number' },
    { key: 'is_highlighted', label: 'Destacada', format: 'boolean' },
    { key: 'featured_on_home', label: 'En Home', format: 'boolean' },
  ],
  fields: [
    { name: 'name', label: 'Nombre', type: 'text', required: true },
    {
      name: 'type',
      label: 'Tipo',
      type: 'select',
      required: true,
      options: [
        { value: 'technical', label: 'Técnica' },
        { value: 'transferable', label: 'Transferible' },
        { value: 'business', label: 'Negocio' },
      ],
    },
    { name: 'category', label: 'Categoría', type: 'creatable-select' },
    { name: 'level', label: 'Nivel', type: 'creatable-select' },
    { name: 'years_of_experience', label: 'Años de experiencia', type: 'number' },
    { name: 'practice_start_date', label: 'Fecha de inicio de práctica', type: 'date' },
    { name: 'proficiency_score', label: 'Score de dominio (0-100)', type: 'number' },
    { name: 'is_highlighted', label: 'Destacada', type: 'boolean' },
    {
      name: 'featured_on_home',
      label: 'Destacado en home',
      type: 'boolean',
      helpText: 'Su categoría aparecerá como badge en la sección "Stack técnico" del Home.',
    },
    {
      name: 'context_libraries',
      label: 'Librerías / contexto técnico',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'records',
        itemNoun: 'librería',
        addLabel: 'Añadir librería',
        itemFields: [
          { name: 'name', label: 'Nombre', placeholder: 'Ej. React' },
          { name: 'years', label: 'Años de uso', placeholder: 'Ej. 3' },
        ],
      },
      helpText: 'Herramientas o librerías de esta competencia, cada una con su tiempo de uso.',
    },
    {
      name: 'aligned_differentiator_ids',
      label: 'Diferenciadores alineados',
      type: 'fk-multi-select',
      fkResource: 'differentiators',
      fkLabelField: 'pillar_name',
      fullWidth: true,
      placeholder: '— Selecciona diferenciadores —',
      helpText: 'Selecciona los diferenciadores que esta competencia respalda.',
    },
    { name: 'depth_description', label: 'Descripción de profundidad', type: 'textarea', fullWidth: true },
    { name: 'market_gaps', label: 'Brechas de mercado', type: 'textarea', fullWidth: true },
    { name: 'honesty_note', label: 'Nota de honestidad', type: 'textarea', fullWidth: true },
  ],
}

export const certificationsConfig: ResourceConfig = {
  key: 'certifications',
  label: 'Certificaciones',
  labelSingular: 'Certificación',
  genderFeminine: true,
  description:
    'Evidencia formal de un tercero (institución externa) de que una competencia es real - a diferencia de Competencias, que es en gran parte autoevaluación. Enlázala siempre a "ID de competencia relacionada" para no dejarla aislada.',
  columns: [
    { key: 'name', label: 'Nombre' },
    { key: 'institution', label: 'Institución' },
    { key: 'year', label: 'Año', format: 'number' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
  ],
  fields: [
    { name: 'name', label: 'Nombre', type: 'text', required: true },
    { name: 'institution', label: 'Institución', type: 'creatable-select' },
    { name: 'year', label: 'Año', type: 'number' },
    {
      name: 'status',
      label: 'Estado',
      type: 'select',
      options: [
        { value: 'pending', label: 'Pendiente' },
        { value: 'in_progress', label: 'En proceso' },
        { value: 'completed', label: 'Completado' },
      ],
    },
    { name: 'related_competency_id', label: 'Competencia relacionada', type: 'fk-select', fkResource: 'competencies', fkLabelField: 'name' },
    { name: 'description', label: 'Descripción', type: 'textarea', fullWidth: true },
    { name: 'syllabus', label: 'Temario', type: 'textarea', fullWidth: true, helpText: 'Markdown.' },
    {
      name: 'document_url',
      label: 'URL del documento',
      type: 'text',
      fullWidth: true,
      helpText: 'Link al documento (PDF o imagen) de la certificación.',
    },
  ],
}

export const targetRolesConfig: ResourceConfig = {
  key: 'target-roles',
  label: 'Roles Objetivo',
  labelSingular: 'Rol objetivo',
  genderFeminine: false,
  description:
    'Los roles que persigues, priorizados y validados con datos reales de mercado (salario, vacantes activas, fecha de validación). Cada rol activo debe estar sustentado por al menos 2-3 pilares de Diferenciadores - si no, es aspiracional, no objetivo real.',
  columns: [
    { key: 'role_name', label: 'Rol' },
    { key: 'priority_order', label: 'Prioridad', format: 'number' },
    { key: 'salary_median', label: 'Salario mediano', format: 'number' },
    { key: 'current_accessibility', label: 'Accesibilidad' },
    { key: 'is_active', label: 'Activo', format: 'boolean' },
  ],
  fields: [
    { name: 'role_name', label: 'Nombre del rol', type: 'text', required: true },
    { name: 'priority_order', label: 'Prioridad (1-3)', type: 'number' },
    { name: 'salary_min', label: 'Salario mínimo', type: 'number' },
    { name: 'salary_median', label: 'Salario mediano', type: 'number' },
    { name: 'salary_max', label: 'Salario máximo', type: 'number' },
    { name: 'years_experience_required', label: 'Años de experiencia requeridos', type: 'number' },
    { name: 'market_active_vacancies', label: 'Vacantes activas en mercado', type: 'number' },
    { name: 'market_validated_at', label: 'Fecha de validación de mercado', type: 'date' },
    { name: 'current_accessibility', label: 'Accesibilidad actual', type: 'creatable-select' },
    { name: 'is_active', label: 'Activo', type: 'boolean' },
    { name: 'description', label: 'Descripción', type: 'textarea', fullWidth: true },
    {
      name: 'key_requirements',
      label: 'Requisitos clave',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'market_sources',
      label: 'Fuentes de mercado',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'text',
        itemNoun: 'fuente',
        addLabel: 'Añadir fuente',
        textPlaceholder: 'Ej. LinkedIn, Indeed…',
      },
    },
  ],
}

export const workHistoryConfig: ResourceConfig = {
  key: 'work-history',
  label: 'Historial Laboral',
  labelSingular: 'Experiencia laboral',
  genderFeminine: true,
  description:
    'El historial cronológico completo de tu trayectoria: qué implicó cada rol, cómo lo viviste, qué aprendiste. Es la base de la que se destilan Logros y, de ahí, tus Historias STAR - cada rol/etapa se registra aquí primero, nunca se salta directo a una historia.',
  columns: [
    { key: 'company', label: 'Empresa' },
    { key: 'role_title', label: 'Puesto' },
    { key: 'start_date', label: 'Inicio', format: 'date' },
    { key: 'end_date', label: 'Fin', format: 'date' },
    { key: 'contract_type', label: 'Tipo de contrato' },
    { key: 'industry_sector', label: 'Sector' },
  ],
  fields: [
    { name: 'company', label: 'Empresa', type: 'text', required: true },
    { name: 'role_title', label: 'Puesto', type: 'text', required: true },
    { name: 'start_date', label: 'Fecha de inicio', type: 'date' },
    { name: 'end_date', label: 'Fecha de fin', type: 'date' },
    { name: 'people_managed', label: 'Personas a cargo', type: 'creatable-select' },
    { name: 'contract_type', label: 'Tipo de contrato', type: 'creatable-select' },
    { name: 'industry_sector', label: 'Sector de industria', type: 'creatable-select' },
    { name: 'description', label: 'Descripción', type: 'textarea', fullWidth: true },
    { name: 'narrative', label: 'Narrativa', type: 'textarea', fullWidth: true },
    { name: 'learnings', label: 'Aprendizajes', type: 'textarea', fullWidth: true },
    {
      name: 'achievement_ids',
      label: 'Logros',
      type: 'fk-multi-select',
      fkResource: 'achievements',
      fkLabelField: 'title',
      fullWidth: true,
      placeholder: '— Selecciona logros —',
      helpText: 'Selecciona uno o más logros de esta experiencia. El vínculo se guarda en cada logro (work_history_id).',
    },
    {
      name: 'key_metrics',
      label: 'Métricas clave',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'kv',
        itemNoun: 'métrica',
        addLabel: 'Añadir métrica',
        keyLabel: 'Nombre',
        valueLabel: 'Valor',
        keyPlaceholder: 'Ej. Equipo gestionado',
        valuePlaceholder: 'Ej. 13 técnicos y administrativos',
      },
    },
  ],
}

export const achievementsConfig: ResourceConfig = {
  key: 'achievements',
  label: 'Logros',
  labelSingular: 'Logro',
  genderFeminine: false,
  description:
    'Logros cuantificables extraídos de tu Historial Laboral, con métricas de impacto verificables - un logro sin cifra es indistinguible de una responsabilidad narrada. Controla en qué audiencias es visible cada uno (CV, entrevista, portal público). "En Home" marca el ÚNICO logro que se muestra como caso destacado en la Home del portal (solo uno a la vez).',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'evidence_type', label: 'Tipo de evidencia', format: 'badge' },
    { key: 'visible_on_cv', label: 'En CV', format: 'boolean' },
    { key: 'visible_in_interview', label: 'En entrevista', format: 'boolean' },
    { key: 'home', label: 'En Home (logro destacado)', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'work_history_id', label: 'Historial laboral relacionado', type: 'fk-select', fkResource: 'work-history', fkLabelField: ['company', 'role_title'] },
    {
      name: 'evidence_type',
      label: 'Tipo de evidencia',
      type: 'select',
      options: [
        { value: 'direct_account', label: 'Relato directo' },
        { value: 'public_backed', label: 'Respaldado públicamente' },
      ],
    },
    { name: 'visible_on_cv', label: 'Visible en CV', type: 'boolean' },
    { name: 'visible_in_interview', label: 'Visible en entrevista', type: 'boolean' },
    { name: 'visible_on_portal', label: 'Visible en portal público', type: 'boolean' },
    {
      name: 'home',
      label: 'Mostrar en Home (logro destacado)',
      type: 'boolean',
      helpText: 'Solo debe haber uno marcado a la vez - es el logro que se muestra como caso destacado en la Home del portal.',
    },
    { name: 'challenge', label: 'Desafío', type: 'textarea', fullWidth: true },
    { name: 'solution', label: 'Solución', type: 'textarea', fullWidth: true },
    { name: 'executive_storytelling', label: 'Narrativa ejecutiva', type: 'textarea', fullWidth: true },
    {
      name: 'documentation_urls',
      label: 'URLs de documentación',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'demonstrated_competency_ids',
      label: 'Competencias demostradas',
      type: 'fk-multi-select',
      fkResource: 'competencies',
      fkLabelField: 'name',
      fullWidth: true,
      placeholder: '— Selecciona competencias —',
      helpText: 'Selecciona las competencias que este logro demuestra.',
    },
    {
      name: 'context',
      label: 'Contexto',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'kv',
        itemNoun: 'dato',
        addLabel: 'Añadir dato',
        keyLabel: 'Aspecto',
        valueLabel: 'Detalle',
        keyPlaceholder: 'Ej. Cliente, sector, entorno…',
        valuePlaceholder: 'Describe ese aspecto',
      },
    },
    {
      name: 'impact_metrics',
      label: 'Métricas de impacto',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'kv',
        itemNoun: 'métrica',
        addLabel: 'Añadir métrica',
        keyLabel: 'Nombre',
        valueLabel: 'Valor',
        keyPlaceholder: 'Ej. Tiempo de resolución',
        valuePlaceholder: 'Ej. 15 minutos vs. 1 año',
      },
    },
  ],
}

export const starStoriesConfig: ResourceConfig = {
  key: 'star-stories',
  label: 'Historias STAR',
  labelSingular: 'Historia STAR',
  genderFeminine: true,
  description:
    'Tu repertorio de máximo 4 historias activas (60-90 segundos), listas para decirse en voz alta bajo presión, cubriendo 4 ángulos distintos (éxito, conflicto, proyecto complejo, error/aprendizaje). Si un logro nuevo es más fuerte, reemplaza a la más débil - nunca se acumula una quinta.',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'duration_seconds', label: 'Duración (s)', format: 'number' },
    { key: 'times_practiced', label: 'Veces practicada', format: 'number' },
    { key: 'active_in_interviews', label: 'Activa', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'duration_seconds', label: 'Duración en segundos (60-90)', type: 'number' },
    { name: 'achievement_id', label: 'Logro relacionado', type: 'fk-select', fkResource: 'achievements', fkLabelField: 'title' },
    { name: 'cross_pattern', label: 'Patrón transversal', type: 'creatable-select' },
    { name: 'times_practiced', label: 'Veces practicada', type: 'number' },
    { name: 'active_in_interviews', label: 'Activa en entrevistas', type: 'boolean' },
    { name: 'narrative', label: 'Narrativa', type: 'textarea', fullWidth: true },
    { name: 'role_application', label: 'Aplicación al rol', type: 'textarea', fullWidth: true },
    { name: 'key_points', label: 'Puntos clave', type: 'textarea', fullWidth: true },
  ],
}

export const careerReviewsConfig: ResourceConfig = {
  key: 'career-reviews',
  label: 'Revisiones de Carrera',
  labelSingular: 'Revisión',
  genderFeminine: true,
  description:
    'Bitácora cronológica de decisiones, hallazgos y aprendizajes de tu evolución de carrera - le da al sistema memoria de proceso, no solo de resultado final. Registra aquí cada hito antes de propagarlo a Identidad o Análisis de Brechas.',
  columns: [
    { key: 'review_date', label: 'Fecha', format: 'date' },
    { key: 'review_type', label: 'Tipo', format: 'badge' },
    { key: 'tracking_status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'review_date', label: 'Fecha de revisión', type: 'date' },
    {
      name: 'review_type',
      label: 'Tipo de revisión',
      type: 'select',
      options: [
        { value: 'gap_analysis', label: 'Análisis de brechas' },
        { value: 'transition_decision', label: 'Decisión de transición' },
        { value: 'quarterly_review', label: 'Revisión trimestral' },
      ],
    },
    {
      name: 'tracking_status',
      label: 'Estado de seguimiento',
      type: 'select',
      options: [
        { value: 'active', label: 'Activa' },
        { value: 'completed', label: 'Completada' },
        { value: 'paused', label: 'Pausada' },
      ],
    },
    { name: 'context', label: 'Contexto', type: 'textarea', fullWidth: true },
    { name: 'decision_or_finding', label: 'Decisión / hallazgo', type: 'textarea', fullWidth: true },
    { name: 'result_or_learning', label: 'Resultado / aprendizaje', type: 'textarea', fullWidth: true },
    {
      name: 'action_items',
      label: 'Acciones a tomar',
      type: 'textarea',
      fullWidth: true,
    },
  ],
}

export const roleGapAnalysisConfig: ResourceConfig = {
  key: 'role-gap-analysis',
  label: 'Análisis de Brechas',
  labelSingular: 'Brecha',
  genderFeminine: true,
  description:
    'Brechas contra los requisitos reales de mercado de cada Rol Objetivo, con severidad, viabilidad y plan de cierre. Cuando Competencias o Certificaciones cierran una brecha, actualízala aquí explícitamente a "Completada" - no lo dejes implícito.',
  columns: [
    { key: 'gap_name', label: 'Brecha' },
    { key: 'severity', label: 'Severidad', format: 'badge' },
    { key: 'viability', label: 'Viabilidad', format: 'badge' },
    { key: 'closure_status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'target_role_id', label: 'Rol objetivo', type: 'fk-select', fkResource: 'target-roles', fkLabelField: 'role_name', required: true },
    { name: 'gap_name', label: 'Nombre de la brecha', type: 'text', required: true },
    {
      name: 'severity',
      label: 'Severidad',
      type: 'select',
      options: [
        { value: 'critical', label: 'Crítica' },
        { value: 'high', label: 'Alta' },
        { value: 'medium', label: 'Media' },
        { value: 'low', label: 'Baja' },
      ],
    },
    {
      name: 'viability',
      label: 'Viabilidad',
      type: 'select',
      options: [
        { value: 'viable', label: 'Viable' },
        { value: 'viable_with_caveats', label: 'Viable con salvedades' },
        { value: 'not_viable', label: 'No viable' },
      ],
    },
    {
      name: 'closure_status',
      label: 'Estado de cierre',
      type: 'select',
      options: [
        { value: 'not_started', label: 'No iniciada' },
        { value: 'in_progress', label: 'En progreso' },
        { value: 'completed', label: 'Completada' },
        { value: 'paused', label: 'Pausada' },
      ],
    },
    { name: 'market_requirement', label: 'Requisito de mercado', type: 'textarea', fullWidth: true },
    { name: 'closing_plan', label: 'Plan de cierre', type: 'textarea', fullWidth: true },
  ],
}

export const projectsConfig: ResourceConfig = {
  key: 'projects',
  label: 'Proyectos',
  labelSingular: 'Proyecto',
  genderFeminine: false,
  description:
    'Tu portafolio de evidencia técnica verificable - 3-5 proyectos bien documentados superan a 10 mediocres. "Destacado" controla el grid de proyectos destacados en la Home.',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'category', label: 'Categoría' },
    { key: 'year', label: 'Año', format: 'number' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'is_featured', label: 'Destacado', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'category', label: 'Categoría', type: 'creatable-select' },
    { name: 'industry', label: 'Industria', type: 'creatable-select' },
    { name: 'year', label: 'Año', type: 'number' },
    {
      name: 'status',
      label: 'Estado',
      type: 'select',
      options: [
        { value: 'active', label: 'Activo' },
        { value: 'in_development', label: 'En desarrollo' },
        { value: 'archived', label: 'Archivado' },
      ],
    },
    { name: 'is_featured', label: 'Destacado (grid de proyectos)', type: 'boolean' },
    { name: 'image_url', label: 'URL de la imagen', type: 'text', fullWidth: true },
    { name: 'github_url', label: 'URL de GitHub', type: 'text' },
    { name: 'demo_url', label: 'URL de demo', type: 'text' },
    { name: 'card_summary', label: 'Resumen para tarjeta (máx. 500)', type: 'textarea', fullWidth: true },
    { name: 'detailed_summary', label: 'Resumen detallado', type: 'textarea', fullWidth: true },
    { name: 'problem', label: 'Problema', type: 'textarea', fullWidth: true },
    { name: 'solution', label: 'Solución', type: 'textarea', fullWidth: true },
    { name: 'architecture', label: 'Arquitectura', type: 'textarea', fullWidth: true },
    { name: 'repo_structure', label: 'Estructura del repositorio', type: 'textarea', fullWidth: true },
    {
      name: 'competency_ids',
      label: 'Stack tecnológico',
      type: 'fk-multi-select',
      fkResource: 'competencies',
      fkLabelField: 'name',
      creatable: true,
      fullWidth: true,
      placeholder: '— Selecciona o escribe una tecnología —',
      helpText:
        'Selecciona competencias existentes o escribe una nueva tecnología para crearla automáticamente en Competencias.',
    },
    {
      name: 'approach_steps',
      label: 'Pasos del enfoque',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'evidence_sources',
      label: 'Fuentes de evidencia',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'metric1_label',
      label: 'Métrica 1 - Nombre',
      type: 'text',
      helpText: 'Ninguna métrica es obligatoria. Hasta 4, cada una con su nombre y valor.',
    },
    { name: 'metric1_value', label: 'Métrica 1 - Valor', type: 'text' },
    { name: 'metric2_label', label: 'Métrica 2 - Nombre', type: 'text' },
    { name: 'metric2_value', label: 'Métrica 2 - Valor', type: 'text' },
    { name: 'metric3_label', label: 'Métrica 3 - Nombre', type: 'text' },
    { name: 'metric3_value', label: 'Métrica 3 - Valor', type: 'text' },
    { name: 'metric4_label', label: 'Métrica 4 - Nombre', type: 'text' },
    { name: 'metric4_value', label: 'Métrica 4 - Valor', type: 'text' },
    {
      name: 'results',
      label: 'Resultados',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'text',
        itemNoun: 'resultado',
        addLabel: 'Añadir resultado',
        textPlaceholder: 'Un resultado medible o hallazgo',
      },
    },
    {
      name: 'releases',
      label: 'Releases',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'records',
        itemNoun: 'versión',
        addLabel: 'Añadir versión',
        itemFields: [
          { name: 'version', label: 'Versión', placeholder: 'v0.1' },
          { name: 'nombre', label: 'Nombre', placeholder: 'Hub Mínimo' },
          { name: 'alcance', label: 'Alcance', type: 'textarea', wide: true, placeholder: 'Qué incluye esta versión' },
        ],
      },
    },
  ],
}

// ---------------------------------------------------------------------------
// Dominio 2: Operativa de Búsqueda
// ---------------------------------------------------------------------------

export const fitScoringFactorsConfig: ResourceConfig = {
  key: 'fit-scoring-factors',
  label: 'Factores de Fit',
  labelSingular: 'Factor de fit',
  genderFeminine: false,
  description:
    'El rubro con el que calculas manualmente el % de fit de cada vacante - los pesos de todos los factores activos deben sumar 100%. Mantenerlo estable evita evaluar el mismo tipo de vacante con criterios distintos en momentos distintos.',
  columns: [
    { key: 'factor_name', label: 'Factor' },
    { key: 'weight_percentage', label: 'Peso %', format: 'number' },
    { key: 'display_order', label: 'Orden', format: 'number' },
  ],
  fields: [
    { name: 'factor_name', label: 'Nombre del factor', type: 'text', required: true },
    { name: 'weight_percentage', label: 'Peso (%)', type: 'number' },
    { name: 'display_order', label: 'Orden de despliegue', type: 'number' },
    { name: 'scoring_guide', label: 'Guía de puntuación', type: 'textarea', fullWidth: true },
  ],
}

export const marketSegmentsConfig: ResourceConfig = {
  key: 'market-segments',
  label: 'Segmentos de Mercado',
  labelSingular: 'Segmento',
  genderFeminine: false,
  description:
    'Los canales de búsqueda (visibles y ocultos) y su prioridad. El mercado oculto (referencias, contacto directo) suele concentrar la mayoría del esfuerzo real, sobre todo en roles senior - revisa periódicamente qué canal convierte mejor y ajusta la prioridad.',
  columns: [
    { key: 'channel_name', label: 'Canal' },
    { key: 'market_type', label: 'Tipo', format: 'badge' },
    { key: 'applications_made', label: 'Aplicaciones', format: 'number' },
    { key: 'interviews_achieved', label: 'Entrevistas', format: 'number' },
    { key: 'is_active', label: 'Activo', format: 'boolean' },
  ],
  fields: [
    { name: 'channel_name', label: 'Nombre del canal', type: 'text' },
    { name: 'channel_type', label: 'Tipo de canal', type: 'creatable-select' },
    {
      name: 'market_type',
      label: 'Tipo de mercado',
      type: 'select',
      options: [
        { value: 'visible', label: 'Visible' },
        { value: 'hidden', label: 'Oculto' },
      ],
    },
    { name: 'priority', label: 'Prioridad (1-10)', type: 'number' },
    { name: 'applications_made', label: 'Aplicaciones realizadas', type: 'number' },
    { name: 'responses_received', label: 'Respuestas recibidas', type: 'number' },
    { name: 'interviews_achieved', label: 'Entrevistas logradas', type: 'number' },
    { name: 'is_active', label: 'Activo', type: 'boolean' },
    { name: 'strategy_text', label: 'Estrategia', type: 'textarea', fullWidth: true },
  ],
}

export const roleNarrativesConfig: ResourceConfig = {
  key: 'role-narratives',
  label: 'Narrativas de Rol',
  labelSingular: 'Narrativa',
  genderFeminine: true,
  description:
    'La capa intermedia entre tu identidad general y los documentos de aplicación: traduce tu posicionamiento vigente a la narrativa específica de cada rol objetivo. De aquí se alimentan CVs, cartas de presentación y entrevistas.',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'usage_context', label: 'Contexto de uso' },
    { key: 'is_active', label: 'Activa', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'target_role_id', label: 'Rol objetivo', type: 'fk-select', fkResource: 'target-roles', fkLabelField: 'role_name' },
    { name: 'usage_context', label: 'Contexto de uso', type: 'creatable-select' },
    { name: 'is_active', label: 'Activa', type: 'boolean' },
    { name: 'full_narrative', label: 'Narrativa completa', type: 'textarea', fullWidth: true },
    { name: 'key_points', label: 'Puntos clave', type: 'textarea', fullWidth: true },
  ],
}

export const searchPlansConfig: ResourceConfig = {
  key: 'search-plans',
  label: 'Planes de Búsqueda',
  labelSingular: 'Plan',
  genderFeminine: false,
  description:
    'El plan ejecutable con timeline, metas cuantitativas y avance real de un periodo de búsqueda. Cierra cada plan con "Aprendizajes" antes de abrir el siguiente periodo - sin eso, el plan nuevo repite los mismos errores sin aprender de los datos ya generados.',
  columns: [
    { key: 'period_start', label: 'Inicio', format: 'date' },
    { key: 'period_end', label: 'Fin', format: 'date' },
    { key: 'plan_status', label: 'Estado', format: 'badge' },
    { key: 'completion_percentage', label: 'Avance %', format: 'number' },
  ],
  fields: [
    { name: 'period_start', label: 'Inicio de periodo', type: 'date' },
    { name: 'period_end', label: 'Fin de periodo', type: 'date' },
    { name: 'target_role_id', label: 'Rol objetivo', type: 'fk-select', fkResource: 'target-roles', fkLabelField: 'role_name' },
    { name: 'target_cvs_sent', label: 'CVs objetivo enviados', type: 'number' },
    { name: 'target_interviews', label: 'Entrevistas objetivo', type: 'number' },
    { name: 'target_offers', label: 'Ofertas objetivo', type: 'number' },
    { name: 'completion_percentage', label: 'Porcentaje de avance', type: 'number' },
    {
      name: 'plan_status',
      label: 'Estado del plan',
      type: 'select',
      options: [
        { value: 'not_started', label: 'No iniciado' },
        { value: 'in_progress', label: 'En progreso' },
        { value: 'paused', label: 'Pausado' },
        { value: 'completed', label: 'Completado' },
        { value: 'cancelled', label: 'Cancelado' },
      ],
    },
    { name: 'lessons_learned', label: 'Aprendizajes', type: 'textarea', fullWidth: true },
    {
      name: 'primary_channels',
      label: 'Canales primarios',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'weekly_targets',
      label: 'Objetivos semanales',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'kv',
        itemNoun: 'objetivo',
        addLabel: 'Añadir objetivo',
        keyLabel: 'Semana',
        valueLabel: 'Objetivo',
        keyPlaceholder: 'Ej. Semana 1',
        valuePlaceholder: 'Ej. 10 aplicaciones enviadas',
      },
    },
  ],
}

export const networkingContactsConfig: ResourceConfig = {
  key: 'networking-contacts',
  label: 'Contactos',
  labelSingular: 'Contacto',
  genderFeminine: false,
  description:
    'Tu matriz de contactos profesionales, categorizados por tipo (reclutador, par técnico, hiring manager) porque el mensaje correcto para uno es el peor para otro. Regla central: aportar valor antes de pedir algo (framework 70-20-10).',
  columns: [
    { key: 'name', label: 'Nombre' },
    { key: 'role_title', label: 'Puesto' },
    { key: 'company_or_specialty', label: 'Empresa / especialidad' },
    { key: 'role_category', label: 'Categoría', format: 'badge' },
    { key: 'contact_status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'name', label: 'Nombre', type: 'text', required: true },
    { name: 'role_title', label: 'Puesto', type: 'text' },
    { name: 'company_or_specialty', label: 'Empresa o especialidad', type: 'text' },
    { name: 'linkedin_url', label: 'URL de LinkedIn', type: 'text' },
    { name: 'email', label: 'Email', type: 'text' },
    {
      name: 'role_category',
      label: 'Categoría de rol',
      type: 'select',
      options: [
        { value: 'data_director', label: 'Director de datos' },
        { value: 'automation_ai_peer', label: 'Par en automatización/IA' },
        { value: 'manager_team_lead', label: 'Manager / líder de equipo' },
        { value: 'specialized_recruiter', label: 'Reclutador especializado' },
        { value: 'target_company_lead', label: 'Contacto en empresa diana' },
      ],
    },
    {
      name: 'contact_status',
      label: 'Estado del contacto',
      type: 'select',
      options: [
        { value: 'pending', label: 'Pendiente' },
        { value: 'contacted', label: 'Contactado' },
        { value: 'following_up', label: 'En seguimiento' },
        { value: 'converted', label: 'Convertido' },
      ],
    },
    { name: 'how_originated', label: 'Cómo se originó', type: 'textarea', fullWidth: true },
    { name: 'notes', label: 'Notas', type: 'textarea', fullWidth: true },
  ],
}

export const targetCompaniesConfig: ResourceConfig = {
  key: 'target-companies',
  label: 'Empresas Diana',
  labelSingular: 'Empresa diana',
  genderFeminine: true,
  description:
    'Empresas objetivo con su tier, rango salarial y el contacto ("weak tie") que las hace accesibles. Prioriza las que ya tienen un contacto asignado - convierten mucho mejor que una aplicación fría sin ningún vínculo.',
  columns: [
    { key: 'company_name', label: 'Empresa' },
    { key: 'tier', label: 'Tier', format: 'number' },
    { key: 'priority', label: 'Prioridad' },
    { key: 'status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'company_name', label: 'Nombre de la empresa', type: 'text', required: true },
    { name: 'tier', label: 'Tier', type: 'number' },
    { name: 'best_fit_role_id', label: 'Rol mejor ajuste', type: 'fk-select', fkResource: 'target-roles', fkLabelField: 'role_name' },
    { name: 'company_size', label: 'Tamaño de empresa', type: 'creatable-select' },
    { name: 'salary_estimate', label: 'Estimado salarial', type: 'creatable-select' },
    { name: 'work_modality', label: 'Modalidad de trabajo', type: 'creatable-select' },
    { name: 'target_market', label: 'Mercado objetivo', type: 'creatable-select' },
    { name: 'weak_tie_contact_id', label: 'Contacto (weak tie)', type: 'fk-select', fkResource: 'networking-contacts', fkLabelField: 'name' },
    { name: 'priority', label: 'Prioridad', type: 'creatable-select' },
    { name: 'status', label: 'Estado', type: 'creatable-select' },
    { name: 'notes', label: 'Notas', type: 'textarea', fullWidth: true },
    {
      name: 'career_board_provider',
      label: 'Board de empleos',
      type: 'select',
      options: [
        { value: 'greenhouse', label: 'Greenhouse' },
        { value: 'lever', label: 'Lever' },
      ],
    },
    {
      name: 'career_board_token',
      label: 'Token / slug del board',
      type: 'text',
      helpText: 'Ej. stripe en boards.greenhouse.io/stripe o jobs.lever.co/stripe',
    },
  ],
}

export const vacanciesConfig: ResourceConfig = {
  key: 'vacancies',
  label: 'Vacantes',
  labelSingular: 'Vacante',
  genderFeminine: true,
  description:
    'Triage de cada oportunidad antes de invertir tiempo en materiales: rol objetivo, % de fit real (calculado con Factores de Fit), rango salarial. Solo si pasa el filtro (60-70% de encaje) avanza a construir CV/carta y aplicar.',
  columns: [
    { key: 'company', label: 'Empresa' },
    { key: 'exact_role', label: 'Rol' },
    { key: 'fit_percentage', label: 'Fit %', format: 'badge', badgeColor: fitBadge },
    { key: 'evaluation', label: 'Evaluación', format: 'badge', badgeColor: badgeByEvaluation },
    { key: 'found_date', label: 'Encontrada', format: 'date' },
    { key: 'is_active', label: 'Activa', format: 'boolean' },
  ],
  fields: [
    { name: 'company', label: 'Empresa', type: 'text', required: true },
    { name: 'exact_role', label: 'Rol exacto', type: 'text', required: true },
    { name: 'order_number', label: 'Número de orden', type: 'number' },
    { name: 'vacancy_url', label: 'URL de la vacante', type: 'text', fullWidth: true },
    { name: 'source', label: 'Fuente', type: 'creatable-select' },
    { name: 'found_date', label: 'Fecha en que se encontró', type: 'date' },
    { name: 'fit_percentage', label: 'Porcentaje de fit (0-100)', type: 'number' },
    { name: 'track_category', label: 'Categoría de track', type: 'creatable-select' },
    { name: 'recommended_cv_version', label: 'Versión de CV recomendada', type: 'creatable-select' },
    {
      name: 'evaluation',
      label: 'Evaluación',
      type: 'select',
      options: [
        { value: 'apply', label: 'Aplicar' },
        { value: 'do_not_apply', label: 'No aplicar' },
        { value: 'pending_review', label: 'Pendiente de revisión' },
      ],
    },
    { name: 'is_active', label: 'Activa', type: 'boolean' },
    { name: 'analysis_notes', label: 'Notas de análisis', type: 'textarea', fullWidth: true },
  ],
}

export const cvVersionsConfig: ResourceConfig = {
  key: 'cv-versions',
  label: 'Versiones de CV',
  labelSingular: 'Versión de CV',
  genderFeminine: true,
  description:
    'Cada dato aquí tiene fuente obligatoria en otra tabla (Identidad, Historial, Logros, Competencias) - nunca redactado de memoria ni con nivel inflado. Un CV ya aprobado no se actualiza automáticamente si su fuente cambia después.',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'length_pages', label: 'Páginas', format: 'number' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'target_role_id', label: 'Rol objetivo', type: 'fk-select', fkResource: 'target-roles', fkLabelField: 'role_name' },
    { name: 'length_pages', label: 'Número de páginas', type: 'number' },
    {
      name: 'status',
      label: 'Estado',
      type: 'select',
      options: [
        { value: 'draft', label: 'Borrador' },
        { value: 'approved', label: 'Aprobado' },
        { value: 'final', label: 'Final' },
      ],
    },
    {
      name: 'target_vacancy_ids',
      label: 'Vacantes objetivo',
      type: 'fk-multi-select',
      fkResource: 'vacancies',
      fkLabelField: 'position_title',
      fullWidth: true,
      placeholder: '— Selecciona vacantes —',
      helpText: 'Selecciona las vacantes a las que apunta esta versión de CV.',
    },
    {
      name: 'content',
      label: 'Contenido',
      type: 'textarea',
      fullWidth: true,
      helpText: 'Markdown - se usa tal cual para generar el PDF (ver botón "Generar PDF").',
    },
  ],
  pdfExportField: 'content',
}

export const pdfOutputTemplatesConfig: ResourceConfig = {
  key: 'pdf-output-templates',
  label: 'Plantillas PDF',
  labelSingular: 'Plantilla PDF',
  genderFeminine: true,
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'document_type', label: 'Tipo', format: 'badge' },
    { key: 'slug', label: 'Slug' },
    { key: 'style_id', label: 'Estilo' },
    { key: 'is_default', label: 'Default', format: 'boolean' },
    { key: 'is_active', label: 'Activa', format: 'boolean' },
  ],
  fields: [
    { name: 'slug', label: 'Slug', type: 'text', required: true, placeholder: 'ej. cv-moderno' },
    {
      name: 'document_type',
      label: 'Tipo de documento',
      type: 'select',
      required: true,
      options: [
        { value: 'cv', label: 'cv' },
        { value: 'cover-letter', label: 'cover-letter' },
        { value: 'generic', label: 'generic' },
      ],
    },
    { name: 'title', label: 'Título', type: 'text', required: true },
    {
      name: 'description',
      label: 'Descripción',
      type: 'text',
      fullWidth: true,
      placeholder: 'Uso previsto (opcional)',
    },
    {
      name: 'style_id',
      label: 'Estilo CSS',
      type: 'fk-select',
      fkResource: 'pdf-template-styles',
      fkApi: 'pdf-template-styles',
      fkLabelField: 'title',
      fullWidth: true,
      placeholder: '— Selecciona un estilo CSS —',
      helpText: 'El CSS vive en Estilos PDF (pds-N). Elige cuál aplicar a esta plantilla.',
    },
    {
      name: 'variables',
      label: 'Variables',
      type: 'textarea',
      fullWidth: true,
      helpText: 'Markdown: documenta cada variable {{nombre}} usada en la plantilla y qué contenido debe llevar.',
    },
    {
      name: 'html_template',
      label: 'Plantilla HTML',
      type: 'code',
      required: true,
      fullWidth: true,
      helpText: 'HTML con variables {{title}}, {{content}}, etc.',
    },
    { name: 'is_default', label: 'Plantilla predeterminada para este tipo', type: 'boolean' },
    { name: 'is_active', label: 'Activa', type: 'boolean' },
  ],
  pdfExportField: 'html_template',
  pdfPreviewSource: 'template-render',
  pdfPreviewHiddenFields: ['html_template', 'variables'],
}

export const pdfTemplateStylesConfig: ResourceConfig = {
  key: 'pdf-template-styles',
  label: 'Estilos PDF',
  labelSingular: 'Estilo PDF',
  genderFeminine: false,
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'slug', label: 'Slug' },
    { key: 'is_active', label: 'Activo', format: 'boolean' },
  ],
  fields: [
    { name: 'slug', label: 'Slug', type: 'text', required: true, placeholder: 'ej. cv-cyan-profesional' },
    { name: 'title', label: 'Título', type: 'text', required: true },
    {
      name: 'description',
      label: 'Descripción',
      type: 'text',
      fullWidth: true,
      placeholder: 'Uso previsto del estilo (opcional)',
    },
    {
      name: 'css_content',
      label: 'CSS',
      type: 'code',
      required: true,
      fullWidth: true,
      helpText: 'Reglas WeasyPrint completas para las plantillas que referencien este estilo.',
    },
    {
      name: 'style_guide',
      label: 'Guía de clases y etiquetas',
      type: 'textarea',
      fullWidth: true,
      helpText: 'Markdown: documenta clases, etiquetas y selectores disponibles y para qué sirven al armar plantillas.',
    },
    { name: 'is_active', label: 'Activo', type: 'boolean' },
  ],
}

export const coverLetterVersionsConfig: ResourceConfig = {
  key: 'cover-letter-versions',
  label: 'Cartas de Presentación',
  labelSingular: 'Carta',
  genderFeminine: true,
  description:
    'Estructura de 3 partes: apertura específica al rol+empresa (nunca genérica), fundamento de experiencia con un ejemplo concreto de Logros, cierre. Nunca repite el CV literalmente - lo complementa.',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'target_role_id', label: 'Rol objetivo', type: 'fk-select', fkResource: 'target-roles', fkLabelField: 'role_name' },
    { name: 'target_vacancy_id', label: 'Vacante objetivo', type: 'fk-select', fkResource: 'vacancies', fkLabelField: 'position_title' },
    {
      name: 'status',
      label: 'Estado',
      type: 'select',
      options: [
        { value: 'draft', label: 'Borrador' },
        { value: 'approved', label: 'Aprobado' },
        { value: 'final', label: 'Final' },
      ],
    },
    { name: 'body_content', label: 'Contenido', type: 'textarea', fullWidth: true },
  ],
}

export const applicationsConfig: ResourceConfig = {
  key: 'applications',
  label: 'Aplicaciones',
  labelSingular: 'Aplicación',
  genderFeminine: true,
  description:
    'Una fila por cada postulación real enviada, enlazando la vacante, el CV y la carta usados. "Estado actual" debe mantenerse vivo - un estado desactualizado rompe el análisis de qué está funcionando.',
  columns: [
    { key: 'vacancy_id', label: 'Vacante' },
    { key: 'applied_at', label: 'Aplicado el', format: 'datetime' },
    { key: 'current_status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'final_result', label: 'Resultado final', format: 'badge' },
  ],
  fields: [
    { name: 'vacancy_id', label: 'Vacante', type: 'fk-select', fkResource: 'vacancies', fkLabelField: 'position_title', required: true },
    { name: 'applied_at', label: 'Fecha/hora de aplicación', type: 'datetime' },
    { name: 'cv_version_id', label: 'Versión de CV', type: 'fk-select', fkResource: 'cv-versions', fkLabelField: 'title' },
    { name: 'cover_letter_version_id', label: 'Versión de carta de presentación', type: 'fk-select', fkResource: 'cover-letter-versions', fkLabelField: 'title' },
    { name: 'recruiter_contact_id', label: 'Contacto reclutador', type: 'fk-select', fkResource: 'networking-contacts', fkLabelField: 'name' },
    {
      name: 'current_status',
      label: 'Estado actual',
      type: 'select',
      options: [
        { value: 'applied', label: 'Aplicado' },
        { value: 'in_process', label: 'En proceso' },
        { value: 'offer', label: 'Oferta' },
        { value: 'rejected', label: 'Rechazado' },
        { value: 'archived', label: 'Archivado' },
      ],
    },
    {
      name: 'final_result',
      label: 'Resultado final',
      type: 'select',
      options: [
        { value: 'offer_accepted', label: 'Oferta aceptada' },
        { value: 'offer_rejected', label: 'Oferta rechazada' },
        { value: 'rejected', label: 'Rechazado' },
        { value: 'negotiating', label: 'Negociando' },
      ],
    },
  ],
}

export const applicationInteractionsConfig: ResourceConfig = {
  key: 'application-interactions',
  label: 'Interacciones de Aplicación',
  labelSingular: 'Interacción',
  genderFeminine: true,
  description:
    'Cada paso posterior a una aplicación (respuesta, llamada, prueba técnica), uno por fila - nunca se sobreescribe la anterior. Es el detalle día a día debajo del estado agregado de Aplicaciones.',
  columns: [
    { key: 'interaction_at', label: 'Fecha', format: 'datetime' },
    { key: 'channel', label: 'Canal' },
    { key: 'status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'application_id', label: 'Aplicación', type: 'fk-select', fkResource: 'applications', fkLabelField: 'company', required: true },
    { name: 'interaction_at', label: 'Fecha/hora', type: 'datetime' },
    { name: 'channel', label: 'Canal', type: 'creatable-select' },
    { name: 'status', label: 'Estado', type: 'creatable-select' },
    { name: 'content_sent', label: 'Contenido enviado', type: 'textarea', fullWidth: true },
    { name: 'response_received', label: 'Respuesta recibida', type: 'textarea', fullWidth: true },
  ],
}

export const interviewsConfig: ResourceConfig = {
  key: 'interviews',
  label: 'Entrevistas',
  labelSingular: 'Entrevista',
  genderFeminine: true,
  description:
    'Registro y preparación de cada entrevista. Distingue lo generalizable (debería mejorar tus Historias STAR) de lo específico de esa empresa puntual, que se queda registrado solo aquí.',
  columns: [
    { key: 'interview_type', label: 'Tipo' },
    { key: 'scheduled_at', label: 'Programada', format: 'datetime' },
    { key: 'overall_impression', label: 'Impresión', format: 'badge' },
    { key: 'interview_result', label: 'Resultado', format: 'badge' },
  ],
  fields: [
    { name: 'application_id', label: 'Aplicación', type: 'fk-select', fkResource: 'applications', fkLabelField: 'company', required: true },
    { name: 'interview_type', label: 'Tipo de entrevista', type: 'creatable-select' },
    { name: 'scheduled_at', label: 'Fecha/hora programada', type: 'datetime' },
    { name: 'narrative_used_id', label: 'Narrativa usada', type: 'fk-select', fkResource: 'role-narratives', fkLabelField: 'title' },
    {
      name: 'overall_impression',
      label: 'Impresión general',
      type: 'select',
      options: [
        { value: 'very_positive', label: 'Muy positiva' },
        { value: 'positive', label: 'Positiva' },
        { value: 'neutral', label: 'Neutral' },
        { value: 'negative', label: 'Negativa' },
      ],
    },
    {
      name: 'interview_result',
      label: 'Resultado',
      type: 'select',
      options: [
        { value: 'pending', label: 'Pendiente' },
        { value: 'advanced', label: 'Avanzó' },
        { value: 'rejected', label: 'Rechazada' },
        { value: 'under_consideration', label: 'En consideración' },
      ],
    },
    { name: 'feedback_received', label: 'Feedback recibido', type: 'textarea', fullWidth: true },
    {
      name: 'interviewers',
      label: 'Entrevistadores',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'questions_asked',
      label: 'Preguntas realizadas',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'answers_given',
      label: 'Respuestas dadas',
      type: 'textarea',
      fullWidth: true,
    },
  ],
}

export const contactInteractionsConfig: ResourceConfig = {
  key: 'contact-interactions',
  label: 'Interacciones de Contacto',
  labelSingular: 'Interacción',
  genderFeminine: true,
  description:
    'Cada mensaje o intercambio real con un contacto, uno por uno - el detalle día a día debajo del estado agregado de Contactos. Marca "Generó oportunidad" cuando una interacción concreta derive en algo real.',
  columns: [
    { key: 'interaction_at', label: 'Fecha', format: 'datetime' },
    { key: 'channel', label: 'Canal' },
    { key: 'status', label: 'Estado', format: 'badge' },
    { key: 'generated_opportunity', label: 'Generó oportunidad', format: 'boolean' },
  ],
  fields: [
    { name: 'contact_id', label: 'Contacto', type: 'fk-select', fkResource: 'networking-contacts', fkLabelField: 'name', required: true },
    { name: 'related_vacancy_id', label: 'Vacante relacionada', type: 'fk-select', fkResource: 'vacancies', fkLabelField: 'position_title' },
    { name: 'interaction_at', label: 'Fecha/hora', type: 'datetime' },
    { name: 'channel', label: 'Canal', type: 'creatable-select' },
    { name: 'status', label: 'Estado', type: 'creatable-select' },
    { name: 'generated_opportunity', label: 'Generó oportunidad', type: 'boolean' },
    { name: 'content_sent', label: 'Contenido enviado', type: 'textarea', fullWidth: true },
    { name: 'response_received', label: 'Respuesta recibida', type: 'textarea', fullWidth: true },
  ],
}

export const networkingActivitiesConfig: ResourceConfig = {
  key: 'networking-activities',
  label: 'Actividades de Networking',
  labelSingular: 'Actividad',
  genderFeminine: true,
  description:
    'Catálogo de actividades recurrentes de aportar valor (comentar posts, compartir contenido), clasificadas en el framework 70-20-10. "Veces realizada" mide disciplina real, no intención - actualízalo cada vez que ejecutes la actividad.',
  columns: [
    { key: 'activity_type', label: 'Actividad' },
    { key: 'category', label: 'Categoría', format: 'badge' },
    { key: 'times_completed', label: 'Veces realizada', format: 'number' },
    { key: 'is_active', label: 'Activa', format: 'boolean' },
  ],
  fields: [
    { name: 'activity_type', label: 'Tipo de actividad', type: 'text', required: true },
    {
      name: 'category',
      label: 'Categoría',
      type: 'select',
      options: [
        { value: 'give_value_70', label: 'Dar valor (70%)' },
        { value: 'share_learning_20', label: 'Compartir aprendizaje (20%)' },
        { value: 'talk_about_you_10', label: 'Hablar de ti (10%)' },
      ],
    },
    { name: 'frequency_description', label: 'Frecuencia', type: 'creatable-select' },
    { name: 'times_completed', label: 'Veces realizada', type: 'number' },
    { name: 'is_active', label: 'Activa', type: 'boolean' },
    { name: 'concrete_action', label: 'Acción concreta', type: 'textarea', fullWidth: true },
    { name: 'example', label: 'Ejemplo', type: 'textarea', fullWidth: true },
  ],
}

// ---------------------------------------------------------------------------
// Dominio 3: Presencia Digital
// ---------------------------------------------------------------------------

export const publicationsConfig: ResourceConfig = {
  key: 'publications',
  label: 'Publicaciones',
  labelSingular: 'Publicación',
  genderFeminine: true,
  description:
    'El blog del Portal Público. "Destacado en home" decide si aparece en la tarjeta destacada de Home; "Tags" es la fuente única de la que se derivan los hashtags cuando la publicación también se cruza a LinkedIn (LinkedIn · Publicar).',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'platform', label: 'Plataforma' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'featured_on_home', label: 'Destacado', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'slug', label: 'Slug', type: 'text' },
    { name: 'platform', label: 'Plataforma', type: 'creatable-select', placeholder: 'LinkedIn, Medium, Blog propio...' },
    { name: 'content_type', label: 'Tipo de contenido', type: 'creatable-select' },
    { name: 'reading_minutes', label: 'Minutos de lectura', type: 'number' },
    {
      name: 'status',
      label: 'Estado',
      type: 'select',
      options: [
        { value: 'draft', label: 'Borrador' },
        { value: 'scheduled', label: 'Programado' },
        { value: 'published', label: 'Publicado' },
      ],
    },
    { name: 'featured_on_home', label: 'Destacado en home', type: 'boolean' },
    { name: 'related_project_id', label: 'Proyecto relacionado', type: 'fk-select', fkResource: 'projects', fkLabelField: 'name' },
    { name: 'publication_url', label: 'URL de publicación', type: 'text', fullWidth: true },
    { name: 'published_at', label: 'Fecha de publicación', type: 'datetime' },
    { name: 'views', label: 'Vistas', type: 'number' },
    { name: 'likes_reactions', label: 'Likes / reacciones', type: 'number' },
    { name: 'comments', label: 'Comentarios', type: 'number' },
    { name: 'shares', label: 'Compartidos', type: 'number' },
    { name: 'image_url', label: 'URL de la imagen destacada', type: 'text', fullWidth: true },
    { name: 'excerpt', label: 'Extracto', type: 'textarea', fullWidth: true },
    { name: 'body_content', label: 'Contenido completo', type: 'textarea', fullWidth: true },
    { name: 'tags', label: 'Tags', type: 'textarea', fullWidth: true },
  ],
}

// LinkedIn *profile* content (headline/about/experience/education/...) - not
// to be confused with the "LinkedIn" posting/OAuth tool at /linkedin (see
// Sidebar.tsx), which is a separate standalone page, not a career resource.
export const linkedinProfileConfig: ResourceConfig = {
  key: 'linkedin-profile',
  label: 'Perfil de LinkedIn',
  labelSingular: 'Perfil de LinkedIn',
  genderFeminine: false,
  mode: 'singleton',
  description:
    'Traducción de tu identidad al formato de LinkedIn (headline ~120 caracteres, About 200-300 palabras). Nunca se redacta de forma independiente: el cambio siempre empieza en Identidad y se traduce aquí después.',
  columns: [],
  fields: [
    { name: 'headline', label: 'Headline', type: 'text', fullWidth: true },
    { name: 'profile_url', label: 'URL del perfil', type: 'text' },
    { name: 'location', label: 'Ubicación', type: 'text' },
    { name: 'about', label: 'About', type: 'textarea', fullWidth: true },
    {
      name: 'experience',
      label: 'Experiencia',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'records',
        itemNoun: 'experiencia',
        addLabel: 'Añadir experiencia',
        itemFields: [
          { name: 'title', label: 'Puesto', placeholder: 'Ej. Gerente de Automatización' },
          { name: 'company', label: 'Empresa', placeholder: 'Ej. CYVSA' },
          { name: 'location', label: 'Ubicación', placeholder: 'Ej. Ciudad de México' },
          { name: 'start_date', label: 'Inicio', type: 'date' },
          { name: 'end_date', label: 'Fin', type: 'date' },
          { name: 'description', label: 'Descripción', type: 'textarea', wide: true },
        ],
      },
    },
    {
      name: 'education',
      label: 'Educación',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'records',
        itemNoun: 'estudio',
        addLabel: 'Añadir estudio',
        itemFields: [
          { name: 'degree', label: 'Título', placeholder: 'Ej. Ingeniería Industrial' },
          { name: 'institution', label: 'Institución', placeholder: 'Ej. UNAM' },
          { name: 'field_of_study', label: 'Área de estudio', placeholder: 'Ej. Automatización' },
          { name: 'start_date', label: 'Inicio', type: 'date' },
          { name: 'end_date', label: 'Fin', type: 'date' },
        ],
      },
    },
    { name: 'featured_skills', label: 'Skills destacadas', type: 'textarea', fullWidth: true },
    { name: 'featured_certifications', label: 'Certificaciones destacadas', type: 'textarea', fullWidth: true },
    { name: 'languages', label: 'Idiomas', type: 'textarea', fullWidth: true },
  ],
}

export const githubProfileConfig: ResourceConfig = {
  key: 'github-profile',
  label: 'Perfil de GitHub',
  labelSingular: 'Perfil de GitHub',
  genderFeminine: false,
  mode: 'singleton',
  description:
    'Traducción ultra-comprimida (headline ~160 caracteres) del mismo diferenciador que LinkedIn, más un README de perfil en Markdown con más detalle técnico. Debe decir lo mismo que LinkedIn sobre qué te hace valioso.',
  columns: [],
  fields: [
    { name: 'headline', label: 'Título', type: 'text', fullWidth: true },
    { name: 'username', label: 'Username de GitHub', type: 'text', helpText: 'Necesario para mostrar tus repos en vivo.' },
    { name: 'profile_url', label: 'URL del perfil', type: 'text' },
    { name: 'bio', label: 'Bio', type: 'textarea', fullWidth: true },
    { name: 'readme_markdown', label: 'README principal (Markdown)', type: 'textarea', fullWidth: true },
  ],
}

export const portalHomeConfig: ResourceConfig = {
  key: 'portal-home',
  label: 'Portal · Home',
  labelSingular: 'Home del portal',
  genderFeminine: false,
  mode: 'singleton',
  description: 'Solo el hero de la Home - proyectos y blog destacados ya se leen de sus propias tablas.',
  columns: [],
  fields: [
    { name: 'hero_photo_url', label: 'URL de la foto', type: 'text', fullWidth: true },
    { name: 'hero_title', label: 'Título principal', type: 'text', fullWidth: true },
    { name: 'hero_subtitle', label: 'Subtítulo', type: 'text', fullWidth: true },
    { name: 'hero_intro', label: 'Texto de introducción', type: 'textarea', fullWidth: true },
    {
      name: 'cta1_label',
      label: 'Botón 1 - Texto',
      type: 'text',
      helpText: 'Se muestra como el botón principal del hero.',
    },
    {
      name: 'cta1_url',
      label: 'Botón 1 - Link',
      type: 'text',
      helpText: 'Ruta interna (ej. "/proyectos") o link externo.',
    },
    { name: 'cta2_label', label: 'Botón 2 - Texto', type: 'text' },
    { name: 'cta2_url', label: 'Botón 2 - Link', type: 'text' },
    { name: 'stat1_label', label: 'Estadística 1 - Nombre', type: 'text' },
    { name: 'stat1_value', label: 'Estadística 1 - Valor', type: 'text' },
    { name: 'stat2_label', label: 'Estadística 2 - Nombre', type: 'text' },
    { name: 'stat2_value', label: 'Estadística 2 - Valor', type: 'text' },
    { name: 'stat3_label', label: 'Estadística 3 - Nombre', type: 'text' },
    { name: 'stat3_value', label: 'Estadística 3 - Valor', type: 'text' },
    { name: 'stat4_label', label: 'Estadística 4 - Nombre', type: 'text' },
    { name: 'stat4_value', label: 'Estadística 4 - Valor', type: 'text' },
  ],
}

export const portalAboutConfig: ResourceConfig = {
  key: 'portal-about',
  label: 'Portal · Sobre Mí',
  labelSingular: 'Sobre Mí del portal',
  genderFeminine: false,
  mode: 'singleton',
  description: 'Solo el nombre y la foto - historia, experiencia, skills y certificaciones ya viven en sus propias tablas.',
  columns: [],
  fields: [
    { name: 'photo_url', label: 'URL de la foto', type: 'text', fullWidth: true },
    { name: 'name', label: 'Nombre', type: 'text', fullWidth: true },
  ],
}

export const portalContactConfig: ResourceConfig = {
  key: 'portal-contact',
  label: 'Portal · Contacto',
  labelSingular: 'Contacto del portal',
  genderFeminine: false,
  mode: 'singleton',
  description: 'Página de Contacto y los links del footer (LinkedIn/GitHub se leen de sus propios perfiles).',
  columns: [],
  fields: [
    { name: 'contact_email', label: 'Email de contacto', type: 'text' },
    { name: 'whatsapp', label: 'WhatsApp', type: 'text', placeholder: '+52 55 1234 5678' },
    { name: 'location', label: 'Ubicación', type: 'text' },
    { name: 'availability_status', label: 'Disponibilidad', type: 'text', placeholder: 'Abierto a oportunidades...' },
    { name: 'preferred_contact_method', label: 'Método de contacto preferido', type: 'text' },
    {
      name: 'footer_links',
      label: 'Links del footer',
      type: 'json',
      fullWidth: true,
      jsonList: {
        kind: 'records',
        itemNoun: 'link',
        addLabel: 'Añadir link',
        itemFields: [
          { name: 'label', label: 'Texto', placeholder: 'Ej. Currículum' },
          { name: 'url', label: 'URL', type: 'url', placeholder: 'https://…', wide: true },
        ],
      },
      helpText: 'Cualquier link adicional del footer (LinkedIn/GitHub ya se leen de sus propios perfiles).',
    },
  ],
}

// ---------------------------------------------------------------------------
// Dominio 4: Soporte
// ---------------------------------------------------------------------------

export const tagsConfig: ResourceConfig = {
  key: 'tags',
  label: 'Etiquetas',
  labelSingular: 'Etiqueta',
  genderFeminine: true,
  description:
    'Catálogo editorial de vocabulario controlado - sin relación técnica (FK) con ninguna otra tabla. Existe para evitar variantes sueltas del mismo concepto en campos de texto libre como los tags de Publicaciones.',
  columns: [
    { key: 'tag_name', label: 'Nombre' },
    { key: 'entity_type', label: 'Tipo de entidad' },
    { key: 'is_active', label: 'Activo', format: 'boolean' },
  ],
  fields: [
    { name: 'tag_name', label: 'Nombre del tag', type: 'text', required: true },
    { name: 'entity_type', label: 'Tipo de entidad', type: 'creatable-select' },
    { name: 'color_hex', label: 'Color (hex)', type: 'text', placeholder: '#22bfd4' },
    { name: 'is_active', label: 'Activo', type: 'boolean' },
  ],
}

// ---------------------------------------------------------------------------
// Dominio 5: Metodologías Operativas
// ---------------------------------------------------------------------------

export const operationalMethodologiesConfig: ResourceConfig = {
  key: 'operational-methodologies',
  label: 'Metodologías Operativas',
  labelSingular: 'Metodología Operativa',
  genderFeminine: true,
  description:
    'Instrucciones para el agente sobre cómo trabajar en las distintas tablas de carrera y cómo se relacionan entre ellas - protocolos y frameworks operativos, uno por registro.',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'section', label: 'Sección' },
    { key: 'subsection', label: 'Subsección' },
    { key: 'agent_profile_ids', label: 'Agentes', format: 'agents' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true, fullWidth: true },
    { name: 'section', label: 'Sección', type: 'creatable-select' },
    { name: 'subsection', label: 'Subsección', type: 'creatable-select' },
    {
      name: 'agent_profile_ids',
      label: 'Agentes destinatarios',
      type: 'multi-select',
      fullWidth: true,
      options: allAgentSelectOptions(),
      helpText:
        'Los agentes consultan automáticamente las metodologías que les asignes aquí. Sin selección = compartida (todos los agentes).',
    },
    { name: 'description', label: 'Descripción breve', type: 'textarea', fullWidth: true },
    {
      name: 'content',
      label: 'Instrucciones (Markdown)',
      type: 'textarea',
      required: true,
      fullWidth: true,
      helpText: 'Contenido completo de la metodología/protocolo, en Markdown.',
    },
  ],
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Domain grouping (navigation only)
// ---------------------------------------------------------------------------
// Kept as a separate map (rather than a `domain` field on every ResourceConfig)
// so the 30 resource declarations above stay untouched. Consumed by the
// Sidebar to render a collapsible "Carrera" section grouped exactly as
// validated with the user - do not reshuffle keys between groups.

// 'methodologies' isn't a CAREER_DOMAINS entry - operational-methodologies
// lives under the "Agente IA" sidebar section instead (see Sidebar.tsx),
// since it's the agent's own knowledge base, not a career-domain resource
// Carlos browses the same way as the other 29.
export type CareerDomainKey = 'identity' | 'search' | 'digital' | 'networking' | 'support'

export interface CareerDomainGroup {
  key: CareerDomainKey
  label: string
  icon: LucideIcon
  resourceKeys: string[]
}

export const CAREER_DOMAINS: CareerDomainGroup[] = [
  {
    key: 'identity',
    label: 'Identidad Profesional',
    icon: Compass,
    resourceKeys: [
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
    ],
  },
  {
    key: 'search',
    label: 'Operativa de Búsqueda',
    icon: Search,
    resourceKeys: [
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
    ],
  },
  {
    key: 'digital',
    label: 'Presencia Digital',
    icon: Globe,
    // Publicaciones deliberately goes last, right before the LinkedIn
    // posting tool spliced in below (Sidebar.tsx) - both are "publish
    // content" actions (portfolio blog vs. LinkedIn), kept together.
    resourceKeys: ['linkedin-profile', 'github-profile', 'portal-home', 'portal-about', 'portal-contact', 'publications'],
  },
  {
    key: 'networking',
    label: 'Networking',
    icon: Handshake,
    // `networking-contacts` intentionally lives under "Operativa de Búsqueda"
    // above (matches the approved schema grouping) - not duplicated here.
    resourceKeys: ['contact-interactions', 'networking-activities'],
  },
  {
    key: 'support',
    label: 'Soporte',
    icon: Tag,
    resourceKeys: ['tags'],
  },
]

/** Icon for a career resource in the sidebar. Fallback is a generic circle. */
export const CAREER_RESOURCE_ICONS: Record<string, LucideIcon> = {
  'personal-profile': User,
  differentiators: Sparkles,
  identity: Quote,
  'identity-reflections': Lightbulb,
  competencies: Award,
  certifications: GraduationCap,
  'target-roles': Target,
  'work-history': Briefcase,
  achievements: Trophy,
  'star-stories': Star,
  'career-reviews': ClipboardCheck,
  'role-gap-analysis': GitBranch,
  projects: Folder,
  'fit-scoring-factors': Scale,
  'market-segments': PieChart,
  'role-narratives': BookOpen,
  'search-plans': Map,
  'networking-contacts': Users,
  'target-companies': Building2,
  vacancies: Bookmark,
  'cv-versions': FileText,
  'cover-letter-versions': Mail,
  applications: Send,
  'application-interactions': MessagesSquare,
  interviews: Calendar,
  'contact-interactions': MessageSquare,
  'networking-activities': Activity,
  'linkedin-profile': Linkedin,
  'github-profile': Github,
  'portal-home': Home,
  'portal-about': UserCircle,
  'portal-contact': Mail,
  publications: Newspaper,
  tags: Tag,
  'operational-methodologies': Layers,
}

export function resourceNavIcon(resourceKey: string): LucideIcon {
  return CAREER_RESOURCE_ICONS[resourceKey] ?? Circle
}

/** Table sections (list CRUD). Singletons are a single ficha, not a table. */
export function isTableResource(config: ResourceConfig | undefined): boolean {
  return Boolean(config && config.mode !== 'singleton')
}

export const CAREER_RESOURCES: Record<string, ResourceConfig> = {
  'personal-profile': personalProfileConfig,
  differentiators: differentiatorsConfig,
  identity: identityConfig,
  'identity-reflections': identityReflectionsConfig,
  competencies: competenciesConfig,
  certifications: certificationsConfig,
  'target-roles': targetRolesConfig,
  'work-history': workHistoryConfig,
  achievements: achievementsConfig,
  'star-stories': starStoriesConfig,
  'career-reviews': careerReviewsConfig,
  'role-gap-analysis': roleGapAnalysisConfig,
  projects: projectsConfig,
  'fit-scoring-factors': fitScoringFactorsConfig,
  'market-segments': marketSegmentsConfig,
  'role-narratives': roleNarrativesConfig,
  'search-plans': searchPlansConfig,
  'networking-contacts': networkingContactsConfig,
  'target-companies': targetCompaniesConfig,
  vacancies: vacanciesConfig,
  'cv-versions': cvVersionsConfig,
  'cover-letter-versions': coverLetterVersionsConfig,
  applications: applicationsConfig,
  'application-interactions': applicationInteractionsConfig,
  interviews: interviewsConfig,
  'contact-interactions': contactInteractionsConfig,
  'networking-activities': networkingActivitiesConfig,
  'linkedin-profile': linkedinProfileConfig,
  'github-profile': githubProfileConfig,
  'portal-home': portalHomeConfig,
  'portal-about': portalAboutConfig,
  'portal-contact': portalContactConfig,
  publications: publicationsConfig,
  tags: tagsConfig,
  'operational-methodologies': operationalMethodologiesConfig,
}

/** Spanish table name for a career (or PDF-style) resource key. */
export function resourceTableLabel(resourceKey: string | undefined): string | undefined {
  if (!resourceKey) return undefined
  if (resourceKey === pdfTemplateStylesConfig.key) return pdfTemplateStylesConfig.label
  return CAREER_RESOURCES[resourceKey]?.label
}

export interface SelectFieldMeta {
  /** `tabla Logros` when FK-backed, `lista` when options are hardcoded. */
  source: string
  /** `opción` or `opción múltiple`. */
  cardinality: string
}

/** Caption for select / multi-select field titles in forms and record viewers. */
export function selectFieldMeta(field: FieldConfig): SelectFieldMeta | null {
  const isMulti = field.type === 'multi-select' || field.type === 'fk-multi-select'
  const isFk = field.type === 'fk-select' || field.type === 'fk-multi-select'
  if (field.type === 'creatable-select') {
    return { source: 'lista acumulada', cardinality: 'opción' }
  }
  if (field.type !== 'select' && !isMulti && !isFk) return null
  const cardinality = isMulti ? 'opción múltiple' : 'opción'
  if (isFk) {
    const table = resourceTableLabel(field.fkResource)
    return { source: table ? `tabla ${table}` : 'tabla', cardinality }
  }
  return { source: 'lista', cardinality }
}
