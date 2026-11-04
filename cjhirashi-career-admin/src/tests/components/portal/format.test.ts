import { describe, expect, it } from 'vitest'
import {
  buildTrendRows,
  deltaTone,
  formatDeltaPct,
  formatDuration,
  formatRate,
  rangeLabel,
  shortPath,
} from '@/components/career/portal/format'
import type { PortalTrendPoint } from '@/types/portalAnalytics'

const point = (bucket: string, visits: number, previous?: number): PortalTrendPoint => ({
  bucket,
  visits,
  visitors: visits,
  pageviews: visits,
  engaged_visits: 0,
  previous_visits: previous,
})

describe('formatDuration', () => {
  it.each([
    [null, '—'],
    [800, '800 ms'],
    [12_000, '12 s'],
    [75_000, '1 min 15 s'],
  ])('%s -> %s', (input, expected) => expect(formatDuration(input as number | null)).toBe(expected))
})

describe('formatRate', () => {
  it('muestra porcentaje con un decimal y guion si no hay dato', () => {
    expect(formatRate(0.9444)).toBe('94.4 %')
    expect(formatRate(0)).toBe('0.0 %')
    expect(formatRate(null)).toBe('—')
  })
})

describe('deltaTone', () => {
  const up = { current: 10, previous: 5, delta_abs: 5, delta_pct: 1 }
  const down = { current: 5, previous: 10, delta_abs: -5, delta_pct: -0.5 }
  it('subir es bueno en visitas y malo en rebote', () => {
    expect(deltaTone('visits', up)).toBe('good')
    expect(deltaTone('visits', down)).toBe('bad')
    expect(deltaTone('bounce_rate', up)).toBe('bad')
    expect(deltaTone('bounce_rate', down)).toBe('good')
  })
  it('sin cambio o sin comparación es neutro', () => {
    expect(deltaTone('visits', { current: 1, previous: 1, delta_abs: 0, delta_pct: 0 })).toBe('neutral')
    expect(deltaTone('visits', undefined)).toBe('neutral')
  })
})

describe('formatDeltaPct', () => {
  it('signo explícito, "nuevo" sin base y guion sin comparación', () => {
    expect(formatDeltaPct({ current: 15, previous: 10, delta_abs: 5, delta_pct: 0.5 })).toBe('+50.0 %')
    expect(formatDeltaPct({ current: 5, previous: 10, delta_abs: -5, delta_pct: -0.5 })).toBe('-50.0 %')
    expect(formatDeltaPct({ current: 4, previous: 0, delta_abs: 4, delta_pct: null })).toBe('nuevo')
    expect(formatDeltaPct({ current: 0, previous: 0, delta_abs: 0, delta_pct: null })).toBe('0 %')
    expect(formatDeltaPct(undefined)).toBe('—')
  })
})

describe('buildTrendRows (RF-061 periodo incompleto punteado)', () => {
  const points = [point('2026-11-01', 5, 4), point('2026-11-02', 7, 6), point('2026-11-03', 2, 9)]

  it('separa el tramo en curso y repite el último punto completo para unir las líneas', () => {
    const rows = buildTrendRows(points, '2026-11-03')
    expect(rows.map((r) => r.visits)).toEqual([5, 7, null])
    expect(rows.map((r) => r.visitsIncomplete)).toEqual([null, 7, 2])
  })

  it('sin periodo incompleto, todo es línea continua', () => {
    const rows = buildTrendRows(points, null)
    expect(rows.map((r) => r.visits)).toEqual([5, 7, 2])
    expect(rows.every((r) => r.visitsIncomplete === null)).toBe(true)
  })

  it('si todo el rango está en curso no hay punto de unión', () => {
    const rows = buildTrendRows(points, '2026-11-01')
    expect(rows.map((r) => r.visits)).toEqual([null, null, null])
    expect(rows.map((r) => r.visitsIncomplete)).toEqual([5, 7, 2])
  })

  it('lleva el valor del periodo comparado', () => {
    expect(buildTrendRows(points, null).map((r) => r.previous)).toEqual([4, 6, 9])
    expect(buildTrendRows([point('2026-11-01', 1)], null)[0].previous).toBeNull()
  })
})

describe('rangeLabel y shortPath', () => {
  it('nombra los preajustes y los rangos exactos', () => {
    expect(rangeLabel({ days: 30 })).toBe('Últimos 30 días')
    expect(rangeLabel({ days: 15 })).toBe('Últimos 15 días')
    expect(rangeLabel({ since: '2026-10-01', until: '2026-10-31' })).toBe('2026-10-01 a 2026-10-31')
  })
  it('recorta rutas largas', () => {
    expect(shortPath('/a')).toBe('/a')
    expect(shortPath('/x'.repeat(40))).toHaveLength(38)
  })
})
