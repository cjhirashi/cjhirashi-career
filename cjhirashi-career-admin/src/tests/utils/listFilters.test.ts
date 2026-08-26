import { describe, it, expect } from 'vitest'
import { recordMatchesFilters, hasActiveFilters, NON_COLUMN_FILTER_FIELDS } from '@/utils/listFilters'

describe('recordMatchesFilters', () => {
  it('keeps every row when no filters are set', () => {
    expect(recordMatchesFilters({ evidence_type: 'public_backed' }, {})).toBe(true)
  })

  it('filters a select by any of the chosen values', () => {
    expect(
      recordMatchesFilters({ evidence_type: 'public_backed' }, { evidence_type: ['public_backed', 'direct_account'] })
    ).toBe(true)
    expect(recordMatchesFilters({ evidence_type: 'inferred' }, { evidence_type: ['public_backed'] })).toBe(false)
  })

  it('filters a boolean status by any of the chosen values', () => {
    expect(recordMatchesFilters({ visible_on_cv: true }, { visible_on_cv: ['true'] })).toBe(true)
    expect(recordMatchesFilters({ visible_on_cv: false }, { visible_on_cv: ['true'] })).toBe(false)
    expect(recordMatchesFilters({ visible_on_cv: false }, { visible_on_cv: ['true', 'false'] })).toBe(true)
  })

  it('filters a multi-select by overlap', () => {
    expect(
      recordMatchesFilters({ demonstrated_competency_ids: ['c1', 'c2'] }, { demonstrated_competency_ids: ['c2'] })
    ).toBe(true)
    expect(
      recordMatchesFilters({ demonstrated_competency_ids: ['c1'] }, { demonstrated_competency_ids: ['c9'] })
    ).toBe(false)
  })
})

describe('hasActiveFilters', () => {
  it('ignores empty arrays and blank strings', () => {
    expect(hasActiveFilters({ a: '', b: [] })).toBe(false)
    expect(hasActiveFilters({ a: 'x' })).toBe(true)
  })
})

describe('NON_COLUMN_FILTER_FIELDS', () => {
  it('excludes virtual payload fields such as achievement_ids', () => {
    expect(NON_COLUMN_FILTER_FIELDS.has('achievement_ids')).toBe(true)
  })
})
