/**
 * Metas, embudos y anotaciones de la analítica (SPEC-0010): cómo se traduce lo que escribe
 * el usuario al diccionario `match` que entiende el servidor, y cómo se valida.
 * Las claves de `match` son las de `event_condition` y `goals` en `services/portal_metrics.py`.
 */

export type MatchInput = 'text' | 'event' | 'seconds' | 'number'

export interface MatchTypeSpec {
  value: string
  label: string
  /** Clave dentro de `match`. */
  key: string
  inputLabel: string
  placeholder: string
  input: MatchInput
}

export const EVENT_TYPE_OPTIONS = [
  { value: 'download', label: 'Descarga de archivo' },
  { value: 'form_submit', label: 'Envío de formulario' },
  { value: 'project_open', label: 'Apertura de proyecto' },
  { value: 'outbound', label: 'Enlace saliente' },
  { value: 'click', label: 'Clic' },
] as const

export const GOAL_TYPES: MatchTypeSpec[] = [
  { value: 'event', label: 'Evento', key: 'event_type', inputLabel: 'Tipo de evento', placeholder: '', input: 'event' },
  { value: 'page', label: 'Página vista', key: 'path_prefix', inputLabel: 'La ruta empieza con', placeholder: '/projects/', input: 'text' },
  { value: 'outbound', label: 'Enlace saliente', key: 'url_contains', inputLabel: 'La dirección contiene', placeholder: 'linkedin.com', input: 'text' },
  { value: 'min_active', label: 'Tiempo activo', key: 'ms', inputLabel: 'Segundos activos mínimos', placeholder: '30', input: 'seconds' },
  { value: 'min_pages', label: 'Páginas por visita', key: 'pages', inputLabel: 'Páginas vistas mínimas', placeholder: '3', input: 'number' },
]

/** Un paso de embudo solo puede ser algo que ocurre en un evento. */
export const FUNNEL_STEP_TYPES = GOAL_TYPES.filter((t) => ['event', 'page', 'outbound'].includes(t.value))

export const ANNOTATION_KINDS = [
  { value: 'blog_post', label: 'Post del blog' },
  { value: 'application', label: 'Postulación' },
  { value: 'deploy', label: 'Despliegue' },
  { value: 'other', label: 'Otra' },
] as const

const spec = (type: string): MatchTypeSpec => {
  const found = GOAL_TYPES.find((t) => t.value === type)
  if (!found) throw new Error(`Tipo desconocido: ${type}`)
  return found
}

/** Lo que escribió el usuario -> el `match` del servidor. */
export const buildMatch = (type: string, input: string): Record<string, string | number> => {
  const { key, input: kind } = spec(type)
  const value = input.trim()
  if (kind === 'seconds') return { [key]: Math.round(Number(value) * 1000) }
  if (kind === 'number') return { [key]: Math.round(Number(value)) }
  return { [key]: value }
}

/** El `match` del servidor -> lo que se muestra al editar. */
export const readMatch = (type: string, match: Record<string, unknown> | null | undefined): string => {
  const { key, input: kind } = spec(type)
  const raw = match?.[key]
  if (raw === undefined || raw === null) return ''
  if (kind === 'seconds') return String(Number(raw) / 1000)
  return String(raw)
}

/** Texto de lista: «Página que empieza con /projects/». */
export const describeMatch = (type: string, match: Record<string, unknown> | null | undefined): string => {
  const known = GOAL_TYPES.find((t) => t.value === type)
  if (!known) return type
  const value = readMatch(type, match)
  if (!value) return known.label
  if (known.input === 'event') return `Evento: ${EVENT_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value}`
  if (known.value === 'page') return `Ruta que empieza con ${value}`
  if (known.value === 'outbound') return `Enlace que contiene ${value}`
  if (known.value === 'min_active') return `${value} s activos o más`
  return `${value} páginas o más`
}

/** Mensaje de error del valor escrito, o `null` si es válido. */
export const validateMatchInput = (type: string, input: string): string | null => {
  const { input: kind, value } = spec(type)
  const text = input.trim()
  if (!text) return 'Falta el valor.'
  if (kind === 'seconds' || kind === 'number') {
    const n = Number(text)
    if (!Number.isFinite(n) || n <= 0) return 'Escribe un número mayor que cero.'
    if (kind === 'number' && !Number.isInteger(n)) return 'Escribe un número entero.'
  }
  if (value === 'page' && !text.startsWith('/')) return 'La ruta debe empezar con «/».'
  return null
}

export interface FunnelStepDraft {
  label: string
  type: string
  value: string
}

export interface FunnelStepPayload {
  label: string
  type: string
  match: Record<string, string | number>
}

export const emptyStep = (): FunnelStepDraft => ({ label: '', type: 'page', value: '' })

export const stepsToPayload = (steps: FunnelStepDraft[]): FunnelStepPayload[] =>
  steps.map((s) => ({ label: s.label.trim(), type: s.type, match: buildMatch(s.type, s.value) }))

export const stepsFromApi = (steps: FunnelStepPayload[] | null | undefined): FunnelStepDraft[] =>
  (steps ?? []).map((s) => ({ label: s.label, type: s.type, value: readMatch(s.type, s.match) }))

/** Errores de un embudo; lista vacía = se puede guardar. */
export const validateFunnel = (name: string, steps: FunnelStepDraft[]): string[] => {
  const errors: string[] = []
  if (!name.trim()) errors.push('Falta el nombre del embudo.')
  if (steps.length < 2) errors.push('Un embudo necesita al menos 2 pasos.')
  steps.forEach((s, i) => {
    if (!s.label.trim()) errors.push(`El paso ${i + 1} no tiene nombre.`)
    const problem = validateMatchInput(s.type, s.value)
    if (problem) errors.push(`Paso ${i + 1}: ${problem}`)
  })
  return errors
}

export const moveStep = <T,>(items: T[], from: number, to: number): T[] => {
  if (to < 0 || to >= items.length || from === to) return items
  const next = [...items]
  const [item] = next.splice(from, 1)
  next.splice(to, 0, item)
  return next
}
