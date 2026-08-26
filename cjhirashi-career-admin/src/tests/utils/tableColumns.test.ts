import { describe, it, expect } from 'vitest'
import {
  availableTableColumns,
  columnFromField,
  defaultTableColumns,
  moveColumnKey,
  nameColumnKey,
  pinColumnOrder,
  pinnedColumnKeys,
  resolveVisibleColumns,
  toggleColumnKey,
} from '@/utils/tableColumns'
import { ResourceConfig } from '@/config/careerResources'

const config = {
  key: 'achievements',
  label: 'Logros',
  labelSingular: 'Logro',
  genderFeminine: false,
  columns: [
    { key: 'title', label: 'Título' },
    { key: 'visible_on_cv', label: 'En CV', format: 'boolean' },
  ],
  fields: [
    { name: 'title', label: 'Título', type: 'text', required: true },
    { name: 'visible_on_cv', label: 'Visible en CV', type: 'boolean' },
    { name: 'narrative', label: 'Narrativa', type: 'textarea' },
  ],
} as ResourceConfig

const allowed = new Set(['id', 'title', 'visible_on_cv', 'narrative'])
const pinned = ['id', 'title']

describe('tableColumns', () => {
  it('defaults to id plus declared columns', () => {
    expect(defaultTableColumns(config).map((col) => col.key)).toEqual(['id', 'title', 'visible_on_cv'])
  })

  it('pins id and the name column', () => {
    expect(nameColumnKey(config)).toBe('title')
    expect(pinnedColumnKeys(config)).toEqual(['id', 'title'])
  })

  it('exposes remaining form fields as optional columns', () => {
    expect(availableTableColumns(config).map((col) => col.key)).toEqual([
      'id',
      'title',
      'visible_on_cv',
      'narrative',
    ])
  })

  it('derives truncate format for long text fields', () => {
    expect(columnFromField({ name: 'narrative', label: 'Narrativa', type: 'textarea' }).format).toBe(
      'truncate'
    )
  })

  it('keeps a custom order after the pinned columns', () => {
    const available = availableTableColumns(config)
    expect(
      resolveVisibleColumns(
        available,
        ['narrative', 'visible_on_cv', 'title'],
        ['id', 'title'],
        pinned
      ).map((col) => col.key)
    ).toEqual(['id', 'title', 'narrative', 'visible_on_cv'])
  })

  it('always restores id and name when the selection is empty', () => {
    const available = availableTableColumns(config)
    expect(resolveVisibleColumns(available, [], ['id', 'title'], pinned).map((col) => col.key)).toEqual([
      'id',
      'title',
    ])
  })

  it('does not allow hiding pinned columns', () => {
    expect(toggleColumnKey(['id', 'title', 'narrative'], 'title', pinned, allowed)).toEqual([
      'id',
      'title',
      'narrative',
    ])
  })

  it('moves an unpinned column without touching id or name', () => {
    expect(
      pinColumnOrder(['visible_on_cv', 'narrative', 'title'], pinned, allowed)
    ).toEqual(['id', 'title', 'visible_on_cv', 'narrative'])
    expect(
      moveColumnKey(['id', 'title', 'visible_on_cv', 'narrative'], 'narrative', -1, pinned, allowed)
    ).toEqual(['id', 'title', 'narrative', 'visible_on_cv'])
  })
})
