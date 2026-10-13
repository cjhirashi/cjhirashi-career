import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { CAREER_RESOURCES } from '@/config/careerResources'
import * as careerResources from '@/config/careerResources'

// Spec 007: el contrato JSON es el canon compartido API <-> Admin.
const contract = JSON.parse(
  readFileSync(
    path.resolve(
      __dirname,
      '../../../../.harness/specs/007-vacantes-etapa-y-estado/contracts/process-stage-catalog.json'
    ),
    'utf-8'
  )
) as {
  stages: { value: string; label: string; status: string }[]
  statuses: { value: string; label: string }[]
}

const config = CAREER_RESOURCES.vacancies
const BADGE_COLORS = ['cyan', 'slate', 'success', 'error', 'warning']

// Funciones esperadas del módulo (se leen dinámicamente para que el test falle con un
// mensaje claro, y no con un error de compilación, antes de implementar T-051).
const mod = careerResources as unknown as Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

describe('RF-011: opciones de etapa == contrato (valor, etiqueta, orden)', () => {
  it('VACANCY_STAGE_OPTIONS coincide con el contrato', () => {
    expect(mod.VACANCY_STAGE_OPTIONS).toEqual(
      contract.stages.map((s) => ({ value: s.value, label: s.label }))
    )
  })

  it('el campo process_stage del formulario usa esas opciones', () => {
    const field = config.fields.find((f) => f.name === 'process_stage')
    expect(field?.type).toBe('select')
    expect(field?.options).toEqual(mod.VACANCY_STAGE_OPTIONS)
    expect(config.fields.find((f) => f.name === 'application_status')).toBeUndefined()
  })
})

describe('RF-016: label y helpText literales del selector de etapa', () => {
  it('textos exactos', () => {
    const field = config.fields.find((f) => f.name === 'process_stage')
    expect(field?.label).toBe('Etapa del proceso')
    expect(field?.helpText).toBe(
      'Dónde va esta vacante en tu proceso. Puedes saltar o retroceder etapas. El estado (Por postular / En proceso / Cerrada) se calcula solo.'
    )
  })
})

describe('RF-012/RF-013/RF-014/RF-018: colores y etiquetas', () => {
  const expectedStageColor = (value: string) => {
    if (value === 'hired' || value === 'offer') return 'success'
    if (value === 'rejected') return 'error'
    if (['withdrawn', 'no_response', 'not_applied'].includes(value)) return 'slate'
    return 'warning'
  }

  it('color de cada una de las 13 etapas (RF-013)', () => {
    for (const s of contract.stages) {
      expect(mod.vacancyStageBadgeColor(s.value), s.value).toBe(expectedStageColor(s.value))
    }
  })

  it('color de los 3 estados (RF-012)', () => {
    expect(mod.vacancyStatusBadgeColor('pending')).toBe('slate')
    expect(mod.vacancyStatusBadgeColor('in_process')).toBe('warning')
    expect(mod.vacancyStatusBadgeColor('closed')).toBe('slate')
  })

  it('sólo usa colores de la unión existente de Badge (RF-018)', () => {
    const all = [
      ...contract.stages.map((s) => mod.vacancyStageBadgeColor(s.value)),
      ...contract.statuses.map((s) => mod.vacancyStatusBadgeColor(s.value)),
      mod.vacancyStageBadgeColor(null),
      mod.vacancyStatusBadgeColor('zzz'),
    ]
    for (const color of all) expect(BADGE_COLORS).toContain(color)
  })

  it('etiquetas en español del contrato (RF-014)', () => {
    for (const s of contract.stages) expect(mod.vacancyStageLabel(s.value)).toBe(s.label)
    for (const s of contract.statuses) expect(mod.vacancyStatusLabel(s.value)).toBe(s.label)
    expect(mod.VACANCY_STATUS_LABELS).toEqual(
      Object.fromEntries(contract.statuses.map((s) => [s.value, s.label]))
    )
  })
})

describe('RF-019: respaldo "Sin definir"/slate', () => {
  it.each([null, undefined, '', 'zzz'])('etapa %p', (value) => {
    expect(mod.vacancyStageLabel(value)).toBe('Sin definir')
    expect(mod.vacancyStageBadgeColor(value)).toBe('slate')
  })
  it.each([null, undefined, '', 'zzz'])('estado %p', (value) => {
    expect(mod.vacancyStatusLabel(value)).toBe('Sin definir')
    expect(mod.vacancyStatusBadgeColor(value)).toBe('slate')
  })
})

describe('RF-015: orden exacto de columnas', () => {
  it('Empresa, Rol, Estado, Etapa, En etapa desde, Fit %, Evaluación, Ubicación, Encontrada, Activa', () => {
    expect(config.columns.map((c) => c.key)).toEqual([
      'company',
      'exact_role',
      'vacancy_status',
      'process_stage',
      'process_stage_updated_at',
      'fit_percentage',
      'evaluation',
      'location',
      'found_date',
      'is_active',
    ])
    expect(config.columns.map((c) => c.label)).toEqual([
      'Empresa',
      'Rol',
      'Estado',
      'Etapa',
      'En etapa desde',
      'Fit %',
      'Evaluación',
      'Ubicación',
      'Encontrada',
      'Activa',
    ])
  })

  it('Estado y Etapa son badges con badgeLabel (RF-012, RF-014)', () => {
    const status = config.columns.find((c) => c.key === 'vacancy_status')
    const stage = config.columns.find((c) => c.key === 'process_stage')
    expect(status?.format).toBe('badge')
    expect(stage?.format).toBe('badge')
    expect(status?.badgeLabel?.('closed')).toBe('Cerrada')
    expect(stage?.badgeLabel?.('hr_interview')).toBe('Entrevista RH')
    expect(status?.badgeColor?.('in_process')).toBe('warning')
    expect(stage?.badgeColor?.('hired')).toBe('success')
  })
})

describe('RF-025: "En etapa desde" sólo fecha', () => {
  it('format date y no es campo del formulario', () => {
    const col = config.columns.find((c) => c.key === 'process_stage_updated_at')
    expect(col?.format).toBe('date')
    expect(config.fields.find((f) => f.name === 'process_stage_updated_at')).toBeUndefined()
  })
})

describe('RF-017/RF-020: filtro por Estado sin campo de formulario', () => {
  it('filterFields declara vacancy_status con 3 opciones y no está en fields', () => {
    const filter = config.filterFields?.find((f) => f.name === 'vacancy_status')
    expect(filter?.type).toBe('select')
    expect(filter?.label).toBe('Estado')
    expect(filter?.options).toEqual(
      contract.statuses.map((s) => ({ value: s.value, label: s.label }))
    )
    expect(config.fields.find((f) => f.name === 'vacancy_status')).toBeUndefined()
  })

  it('ningún otro recurso declara filterFields', () => {
    for (const [key, cfg] of Object.entries(CAREER_RESOURCES)) {
      if (key !== 'vacancies') expect(cfg.filterFields, key).toBeUndefined()
    }
  })
})
