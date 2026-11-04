import type { PortalKpiDelta, PortalRange, PortalTrendPoint } from '@/types/portalAnalytics'

export const formatDuration = (ms: number | null | undefined): string => {
  if (ms === null || ms === undefined) return '—'
  if (ms < 1000) return `${ms} ms`
  const totalSeconds = Math.round(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return minutes > 0 ? `${minutes} min ${seconds} s` : `${seconds} s`
}

/** Tasa de 0 a 1 -> "94.4 %"; sin dato -> "—" (no un 0 % engañoso). */
export const formatRate = (value: number | null | undefined): string =>
  value === null || value === undefined ? '—' : `${(value * 100).toFixed(1)} %`

export const formatNumber = (value: number | null | undefined, digits = 0): string =>
  value === null || value === undefined ? '—' : value.toLocaleString('es-MX', { maximumFractionDigits: digits })

export type DeltaTone = 'good' | 'bad' | 'neutral'

/** En estas métricas bajar es mejorar. */
const LOWER_IS_BETTER = new Set(['bounce_rate'])

export const deltaTone = (metric: string, delta: PortalKpiDelta | undefined): DeltaTone => {
  if (!delta || delta.delta_abs === null || delta.delta_abs === 0) return 'neutral'
  const improved = LOWER_IS_BETTER.has(metric) ? delta.delta_abs < 0 : delta.delta_abs > 0
  return improved ? 'good' : 'bad'
}

/** `0.123` -> "+12.3 %"; sin base de comparación (previo 0) -> "nuevo". */
export const formatDeltaPct = (delta: PortalKpiDelta | undefined): string => {
  if (!delta || delta.delta_abs === null) return '—'
  if (delta.delta_pct === null) return delta.delta_abs === 0 ? '0 %' : 'nuevo'
  const pct = delta.delta_pct * 100
  return `${pct > 0 ? '+' : ''}${pct.toFixed(1)} %`
}

export interface TrendRow {
  bucket: string
  visits: number | null
  visitsIncomplete: number | null
  previous: number | null
}

/** Parte la serie en tramo completo (línea continua) y tramo en curso (punteada).
 * El último punto completo se repite en ambos para que las líneas se toquen. */
export const buildTrendRows = (points: PortalTrendPoint[], incompleteFrom: string | null): TrendRow[] => {
  const firstIncomplete = incompleteFrom ? points.findIndex((p) => p.bucket >= incompleteFrom) : -1
  return points.map((p, i) => {
    const incomplete = firstIncomplete !== -1 && i >= firstIncomplete
    const joint = firstIncomplete > 0 && i === firstIncomplete - 1
    return {
      bucket: p.bucket,
      visits: incomplete ? null : p.visits,
      visitsIncomplete: incomplete || joint ? p.visits : null,
      previous: p.previous_visits ?? null,
    }
  })
}

export const RANGE_PRESETS = [
  { days: 7, label: 'Últimos 7 días' },
  { days: 30, label: 'Últimos 30 días' },
  { days: 90, label: 'Últimos 90 días' },
] as const

export const rangeLabel = (range: PortalRange): string =>
  'days' in range ? (RANGE_PRESETS.find((p) => p.days === range.days)?.label ?? `Últimos ${range.days} días`) : `${range.since} a ${range.until}`

export const COMPARE_OPTIONS = [
  { value: 'none', label: 'Sin comparar' },
  { value: 'previous', label: 'Periodo anterior' },
  { value: 'year', label: 'Mismo periodo del año anterior' },
  { value: 'weekday', label: 'Mismos días de la semana' },
] as const

/** "/projects/foo" -> "/projects/foo"; recorta rutas muy largas para tablas angostas. */
export const shortPath = (path: string, max = 38): string => (path.length > max ? `${path.slice(0, max - 1)}…` : path)

export const CHANNEL_LABELS: Record<string, string> = {
  Direct: 'Directo',
  'Organic Search': 'Búsqueda orgánica',
  'Organic Social': 'Redes sociales',
  Email: 'Correo',
  Referral: 'Referencias',
  Paid: 'Pago',
  Application: 'Postulaciones',
  Unknown: 'Desconocido',
}
