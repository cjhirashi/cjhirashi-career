import { describe, it, expect } from 'vitest'
import { matchesRecordSegment, recordSegmentFromPath, recordUrlSegment } from '@/utils/recordUrl'

describe('recordUrl', () => {
  it('prefers slug over id in the path segment', () => {
    expect(recordUrlSegment({ id: 'pdt-1', user_id: 'usr-2', slug: 'cv-ats-optimizado' })).toBe(
      'cv-ats-optimizado'
    )
  })

  it('falls back to id when there is no slug', () => {
    expect(recordUrlSegment({ id: 'cmp-1', user_id: 'usr-2' })).toBe('cmp-1')
  })

  it('matches a record by slug or id', () => {
    const item = { id: 'pdt-1', user_id: 'usr-2', slug: 'cv-ats-optimizado' }
    expect(matchesRecordSegment(item, 'cv-ats-optimizado')).toBe(true)
    expect(matchesRecordSegment(item, 'pdt-1')).toBe(true)
    expect(matchesRecordSegment(item, 'other')).toBe(false)
  })

  it('reads the record segment from a list path prefix', () => {
    expect(recordSegmentFromPath('/agent/pdf-templates', '/agent/pdf-templates')).toBeUndefined()
    expect(recordSegmentFromPath('/agent/pdf-templates/cv-ats-optimizado', '/agent/pdf-templates')).toBe(
      'cv-ats-optimizado'
    )
    expect(recordSegmentFromPath('/career/vacancies/vac-7', '/career/vacancies')).toBe('vac-7')
  })
})
