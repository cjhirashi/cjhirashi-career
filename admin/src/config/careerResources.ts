// ============================================================================
// Declarative configuration for every career-domain (v2) resource.
//
// This is the frontend mirror of the backend's generic CRUD router factory
// (api/src/routes/career_common.py): instead of 24 near-identical page
// components, each resource is described as data (endpoint, table columns,
// form fields) and rendered by the single generic `CareerResourceView`
// component (see src/components/career/CareerResourceView.tsx).
// ============================================================================

import { Compass, Search, Globe, Handshake, Tag, type LucideIcon } from 'lucide-react'

export type FieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'date'
  | 'datetime'
  | 'boolean'
  | 'select'
  | 'string-array' // newline-separated list -> string[]
  | 'number-array' // comma-separated list -> number[]
  | 'json' // raw JSON textarea -> parsed with JSON.parse

export interface SelectOption {
  value: string
  label: string
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
}

export type ColumnFormat = 'text' | 'date' | 'datetime' | 'boolean' | 'badge' | 'truncate' | 'number'

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
  /** UI hint only - CareerResourceView still uses the same fetch/mutate logic. */
  variant?: 'table' | 'cards'
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

export const differentiatorsConfig: ResourceConfig = {
  key: 'differentiators',
  label: 'Diferenciadores',
  labelSingular: 'Diferenciador',
  genderFeminine: false,
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
  columns: [
    { key: 'name', label: 'Nombre' },
    { key: 'type', label: 'Tipo', format: 'badge' },
    { key: 'category', label: 'Categoría' },
    { key: 'level', label: 'Nivel' },
    { key: 'years_of_experience', label: 'Años exp.', format: 'number' },
    { key: 'proficiency_score', label: 'Score', format: 'number' },
    { key: 'is_highlighted', label: 'Destacada', format: 'boolean' },
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
    { name: 'category', label: 'Categoría', type: 'text' },
    { name: 'level', label: 'Nivel', type: 'text' },
    { name: 'years_of_experience', label: 'Años de experiencia', type: 'number' },
    { name: 'practice_start_date', label: 'Fecha de inicio de práctica', type: 'date' },
    { name: 'proficiency_score', label: 'Score de dominio (0-100)', type: 'number' },
    { name: 'is_highlighted', label: 'Destacada', type: 'boolean' },
    {
      name: 'context_libraries',
      label: 'Librerías / contexto técnico (JSON)',
      type: 'json',
      fullWidth: true,
      helpText: 'Estructura libre (ej. lista de librerías con años de uso) - se edita como JSON crudo.',
    },
    {
      name: 'aligned_differentiator_ids',
      label: 'IDs de diferenciadores alineados (separados por coma)',
      type: 'number-array',
      fullWidth: true,
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
  columns: [
    { key: 'name', label: 'Nombre' },
    { key: 'institution', label: 'Institución' },
    { key: 'year', label: 'Año', format: 'number' },
  ],
  fields: [
    { name: 'name', label: 'Nombre', type: 'text', required: true },
    { name: 'institution', label: 'Institución', type: 'text' },
    { name: 'year', label: 'Año', type: 'number' },
    { name: 'related_competency_id', label: 'ID de competencia relacionada', type: 'number' },
    { name: 'description', label: 'Descripción', type: 'textarea', fullWidth: true },
  ],
}

export const targetRolesConfig: ResourceConfig = {
  key: 'target-roles',
  label: 'Roles Objetivo',
  labelSingular: 'Rol objetivo',
  genderFeminine: false,
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
    { name: 'current_accessibility', label: 'Accesibilidad actual', type: 'text' },
    { name: 'is_active', label: 'Activo', type: 'boolean' },
    { name: 'description', label: 'Descripción', type: 'textarea', fullWidth: true },
    {
      name: 'key_requirements',
      label: 'Requisitos clave',
      type: 'textarea',
      fullWidth: true,
    },
    { name: 'market_sources', label: 'Fuentes de mercado (JSON)', type: 'json', fullWidth: true },
  ],
}

export const workHistoryConfig: ResourceConfig = {
  key: 'work-history',
  label: 'Historial Laboral',
  labelSingular: 'Experiencia laboral',
  genderFeminine: true,
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
    { name: 'people_managed', label: 'Personas a cargo', type: 'text' },
    { name: 'contract_type', label: 'Tipo de contrato', type: 'text' },
    { name: 'industry_sector', label: 'Sector de industria', type: 'text' },
    { name: 'description', label: 'Descripción', type: 'textarea', fullWidth: true },
    { name: 'narrative', label: 'Narrativa', type: 'textarea', fullWidth: true },
    { name: 'learnings', label: 'Aprendizajes', type: 'textarea', fullWidth: true },
    {
      name: 'achievements',
      label: 'Logros',
      type: 'textarea',
      fullWidth: true,
    },
    { name: 'key_metrics', label: 'Métricas clave (JSON)', type: 'json', fullWidth: true },
  ],
}

export const achievementsConfig: ResourceConfig = {
  key: 'achievements',
  label: 'Logros',
  labelSingular: 'Logro',
  genderFeminine: false,
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'evidence_type', label: 'Tipo de evidencia', format: 'badge' },
    { key: 'visible_on_cv', label: 'En CV', format: 'boolean' },
    { key: 'visible_in_interview', label: 'En entrevista', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'work_history_id', label: 'ID historial laboral relacionado', type: 'number' },
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
      label: 'IDs de competencias demostradas (separados por coma)',
      type: 'number-array',
      fullWidth: true,
    },
    { name: 'context', label: 'Contexto (JSON)', type: 'json', fullWidth: true },
    { name: 'impact_metrics', label: 'Métricas de impacto (JSON)', type: 'json', fullWidth: true },
  ],
}

export const starStoriesConfig: ResourceConfig = {
  key: 'star-stories',
  label: 'Historias STAR',
  labelSingular: 'Historia STAR',
  genderFeminine: true,
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'duration_seconds', label: 'Duración (s)', format: 'number' },
    { key: 'times_practiced', label: 'Veces practicada', format: 'number' },
    { key: 'active_in_interviews', label: 'Activa', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'duration_seconds', label: 'Duración en segundos (60-90)', type: 'number' },
    { name: 'achievement_id', label: 'ID de logro relacionado', type: 'number' },
    { name: 'cross_pattern', label: 'Patrón transversal', type: 'text' },
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
  columns: [
    { key: 'gap_name', label: 'Brecha' },
    { key: 'severity', label: 'Severidad', format: 'badge' },
    { key: 'viability', label: 'Viabilidad', format: 'badge' },
    { key: 'closure_status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'target_role_id', label: 'ID de rol objetivo', type: 'number', required: true },
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
  variant: 'cards',
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'category', label: 'Categoría' },
    { key: 'year', label: 'Año', format: 'number' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'is_featured', label: 'Destacado', format: 'boolean' },
    { key: 'is_anchor', label: 'Ancla (caso destacado en Home)', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'category', label: 'Categoría', type: 'text' },
    { name: 'industry', label: 'Industria', type: 'text' },
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
    {
      name: 'is_anchor',
      label: 'Ancla (caso de estudio en Home)',
      type: 'boolean',
      helpText: 'Solo debe haber uno marcado como ancla a la vez - es el proyecto que se muestra completo en la Home.',
    },
    { name: 'image_url', label: 'URL de la imagen', type: 'text', fullWidth: true },
    { name: 'github_url', label: 'URL de GitHub', type: 'text' },
    { name: 'demo_url', label: 'URL de demo', type: 'text' },
    { name: 'card_summary', label: 'Resumen para tarjeta (máx. 500)', type: 'textarea', fullWidth: true },
    { name: 'detailed_summary', label: 'Resumen detallado', type: 'textarea', fullWidth: true },
    { name: 'problem', label: 'Problema', type: 'textarea', fullWidth: true },
    { name: 'solution', label: 'Solución', type: 'textarea', fullWidth: true },
    { name: 'architecture', label: 'Arquitectura', type: 'textarea', fullWidth: true },
    { name: 'repo_structure', label: 'Estructura del repositorio', type: 'textarea', fullWidth: true },
    { name: 'tech_stack', label: 'Stack tecnológico', type: 'textarea', fullWidth: true },
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
    { name: 'results', label: 'Resultados (JSON)', type: 'json', fullWidth: true },
    { name: 'releases', label: 'Releases (JSON)', type: 'json', fullWidth: true },
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
  columns: [
    { key: 'channel_name', label: 'Canal' },
    { key: 'market_type', label: 'Tipo', format: 'badge' },
    { key: 'applications_made', label: 'Aplicaciones', format: 'number' },
    { key: 'interviews_achieved', label: 'Entrevistas', format: 'number' },
    { key: 'is_active', label: 'Activo', format: 'boolean' },
  ],
  fields: [
    { name: 'channel_name', label: 'Nombre del canal', type: 'text' },
    { name: 'channel_type', label: 'Tipo de canal', type: 'text' },
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
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'usage_context', label: 'Contexto de uso' },
    { key: 'is_active', label: 'Activa', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'target_role_id', label: 'ID de rol objetivo', type: 'number' },
    { name: 'usage_context', label: 'Contexto de uso', type: 'text' },
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
  columns: [
    { key: 'period_start', label: 'Inicio', format: 'date' },
    { key: 'period_end', label: 'Fin', format: 'date' },
    { key: 'plan_status', label: 'Estado', format: 'badge' },
    { key: 'completion_percentage', label: 'Avance %', format: 'number' },
  ],
  fields: [
    { name: 'period_start', label: 'Inicio de periodo', type: 'date' },
    { name: 'period_end', label: 'Fin de periodo', type: 'date' },
    { name: 'target_role_id', label: 'ID de rol objetivo', type: 'number' },
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
    { name: 'weekly_targets', label: 'Objetivos semanales (JSON)', type: 'json', fullWidth: true },
  ],
}

export const networkingContactsConfig: ResourceConfig = {
  key: 'networking-contacts',
  label: 'Contactos',
  labelSingular: 'Contacto',
  genderFeminine: false,
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
  columns: [
    { key: 'company_name', label: 'Empresa' },
    { key: 'tier', label: 'Tier', format: 'number' },
    { key: 'priority', label: 'Prioridad' },
    { key: 'status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'company_name', label: 'Nombre de la empresa', type: 'text', required: true },
    { name: 'tier', label: 'Tier', type: 'number' },
    { name: 'best_fit_role_id', label: 'ID de rol mejor ajuste', type: 'number' },
    { name: 'company_size', label: 'Tamaño de empresa', type: 'text' },
    { name: 'salary_estimate', label: 'Estimado salarial', type: 'text' },
    { name: 'work_modality', label: 'Modalidad de trabajo', type: 'text' },
    { name: 'target_market', label: 'Mercado objetivo', type: 'text' },
    { name: 'weak_tie_contact_id', label: 'ID de contacto (weak tie)', type: 'number' },
    { name: 'priority', label: 'Prioridad', type: 'text' },
    { name: 'status', label: 'Estado', type: 'text' },
    { name: 'notes', label: 'Notas', type: 'textarea', fullWidth: true },
  ],
}

export const vacanciesConfig: ResourceConfig = {
  key: 'vacancies',
  label: 'Vacantes',
  labelSingular: 'Vacante',
  genderFeminine: true,
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
    { name: 'source', label: 'Fuente', type: 'text' },
    { name: 'found_date', label: 'Fecha en que se encontró', type: 'date' },
    { name: 'fit_percentage', label: 'Porcentaje de fit (0-100)', type: 'number' },
    { name: 'track_category', label: 'Categoría de track', type: 'text' },
    { name: 'recommended_cv_version', label: 'Versión de CV recomendada', type: 'text' },
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
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'length_pages', label: 'Páginas', format: 'number' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'target_role_id', label: 'ID de rol objetivo', type: 'number' },
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
    { name: 'featured_achievement', label: 'Logro destacado', type: 'text', fullWidth: true },
    { name: 'executive_summary', label: 'Resumen ejecutivo', type: 'textarea', fullWidth: true },
    {
      name: 'key_competencies',
      label: 'Competencias clave',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'target_vacancy_ids',
      label: 'IDs de vacantes objetivo (separados por coma)',
      type: 'number-array',
      fullWidth: true,
    },
    {
      name: 'key_experience',
      label: 'Experiencia clave (JSON)',
      type: 'json',
      fullWidth: true,
      helpText: 'Estructura anidada (empresa, logros, métricas por experiencia) - editada como JSON crudo.',
    },
  ],
}

export const coverLetterVersionsConfig: ResourceConfig = {
  key: 'cover-letter-versions',
  label: 'Cartas de Presentación',
  labelSingular: 'Carta',
  genderFeminine: true,
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'target_role_id', label: 'ID de rol objetivo', type: 'number' },
    { name: 'target_vacancy_id', label: 'ID de vacante objetivo', type: 'number' },
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
  columns: [
    { key: 'vacancy_id', label: 'ID vacante', format: 'number' },
    { key: 'applied_at', label: 'Aplicado el', format: 'datetime' },
    { key: 'current_status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'final_result', label: 'Resultado final', format: 'badge' },
  ],
  fields: [
    { name: 'vacancy_id', label: 'ID de vacante', type: 'number', required: true },
    { name: 'applied_at', label: 'Fecha/hora de aplicación', type: 'datetime' },
    { name: 'cv_version_id', label: 'ID de versión de CV', type: 'number' },
    { name: 'cover_letter_version_id', label: 'ID de versión de carta', type: 'number' },
    { name: 'recruiter_contact_id', label: 'ID de contacto reclutador', type: 'number' },
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
  columns: [
    { key: 'interaction_at', label: 'Fecha', format: 'datetime' },
    { key: 'channel', label: 'Canal' },
    { key: 'status', label: 'Estado', format: 'badge' },
  ],
  fields: [
    { name: 'application_id', label: 'ID de aplicación', type: 'number', required: true },
    { name: 'interaction_at', label: 'Fecha/hora', type: 'datetime' },
    { name: 'channel', label: 'Canal', type: 'text' },
    { name: 'status', label: 'Estado', type: 'text' },
    { name: 'content_sent', label: 'Contenido enviado', type: 'textarea', fullWidth: true },
    { name: 'response_received', label: 'Respuesta recibida', type: 'textarea', fullWidth: true },
  ],
}

export const interviewsConfig: ResourceConfig = {
  key: 'interviews',
  label: 'Entrevistas',
  labelSingular: 'Entrevista',
  genderFeminine: true,
  columns: [
    { key: 'interview_type', label: 'Tipo' },
    { key: 'scheduled_at', label: 'Programada', format: 'datetime' },
    { key: 'overall_impression', label: 'Impresión', format: 'badge' },
    { key: 'interview_result', label: 'Resultado', format: 'badge' },
  ],
  fields: [
    { name: 'application_id', label: 'ID de aplicación', type: 'number', required: true },
    { name: 'interview_type', label: 'Tipo de entrevista', type: 'text' },
    { name: 'scheduled_at', label: 'Fecha/hora programada', type: 'datetime' },
    { name: 'narrative_used_id', label: 'ID de narrativa usada', type: 'number' },
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
  columns: [
    { key: 'interaction_at', label: 'Fecha', format: 'datetime' },
    { key: 'channel', label: 'Canal' },
    { key: 'status', label: 'Estado', format: 'badge' },
    { key: 'generated_opportunity', label: 'Generó oportunidad', format: 'boolean' },
  ],
  fields: [
    { name: 'contact_id', label: 'ID de contacto', type: 'number', required: true },
    { name: 'related_vacancy_id', label: 'ID de vacante relacionada', type: 'number' },
    { name: 'interaction_at', label: 'Fecha/hora', type: 'datetime' },
    { name: 'channel', label: 'Canal', type: 'text' },
    { name: 'status', label: 'Estado', type: 'text' },
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
    { name: 'frequency_description', label: 'Frecuencia', type: 'text' },
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
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'platform', label: 'Plataforma' },
    { key: 'status', label: 'Estado', format: 'badge', badgeColor: badgeByStatusGeneric },
    { key: 'featured_on_home', label: 'Destacado', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'slug', label: 'Slug', type: 'text' },
    { name: 'platform', label: 'Plataforma', type: 'text', placeholder: 'LinkedIn, Medium, Blog propio...' },
    { name: 'content_type', label: 'Tipo de contenido', type: 'text' },
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
    { name: 'related_project_id', label: 'ID de proyecto relacionado', type: 'number' },
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
  columns: [],
  fields: [
    { name: 'headline', label: 'Headline', type: 'text', fullWidth: true },
    { name: 'profile_url', label: 'URL del perfil', type: 'text' },
    { name: 'location', label: 'Ubicación', type: 'text' },
    { name: 'about', label: 'About', type: 'textarea', fullWidth: true },
    {
      name: 'experience',
      label: 'Experiencia (JSON)',
      type: 'json',
      fullWidth: true,
      helpText:
        'Lista de objetos: [{"company","title","location","start_date","end_date","description"}, ...]',
    },
    {
      name: 'education',
      label: 'Educación (JSON)',
      type: 'json',
      fullWidth: true,
      helpText: 'Lista de objetos: [{"institution","degree","field_of_study","start_date","end_date"}, ...]',
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
      label: 'Links del footer (JSON)',
      type: 'json',
      fullWidth: true,
      helpText: 'Lista de objetos: [{"label","url"}, ...] - cualquier link adicional del footer.',
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
  columns: [
    { key: 'tag_name', label: 'Nombre' },
    { key: 'entity_type', label: 'Tipo de entidad' },
    { key: 'is_active', label: 'Activo', format: 'boolean' },
  ],
  fields: [
    { name: 'tag_name', label: 'Nombre del tag', type: 'text', required: true },
    { name: 'entity_type', label: 'Tipo de entidad', type: 'text' },
    { name: 'color_hex', label: 'Color (hex)', type: 'text', placeholder: '#22bfd4' },
    { name: 'is_active', label: 'Activo', type: 'boolean' },
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

export const CAREER_RESOURCES: Record<string, ResourceConfig> = {
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
}
