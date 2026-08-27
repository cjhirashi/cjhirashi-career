import { useEffect, useMemo, useState } from 'react'
import { ColumnConfig } from '@/config/careerResources'
import { useVisibleTableColumns } from '@/hooks/useVisibleTableColumns'
import { compareCells, SortState } from '@/utils/tableColumns'
import { ColumnSettingsProps } from '@/components/section/SectionToolbar'

interface UseSectionTableOptions<Row> {
  /** Stable key for persisting column visibility/order in localStorage. */
  storageKey: string
  /** Every column that can be shown. */
  columns: ColumnConfig[]
  /** Columns visible by default (keys). Defaults to all. */
  defaultColumnKeys?: string[]
  /** Columns that cannot be hidden/reordered (keys). Defaults to `['id']`. */
  pinnedKeys?: string[]
  rows: Row[]
  initialSort?: SortState
  /**
   * When provided, the hook filters `rows` client-side by the debounced search
   * text against this accessor. Omit for server-side search (pass filtered
   * `rows` yourself).
   */
  searchAccessor?: (row: Row) => string
  searchDebounceMs?: number
}

/**
 * Bundles the state every section list needs: visible/ordered columns
 * (persisted), sort toggling, and a debounced search box — plus, when a
 * `searchAccessor` is given, the client-side filtered + sorted rows.
 */
export function useSectionTable<Row>({
  storageKey,
  columns,
  defaultColumnKeys,
  pinnedKeys = ['id'],
  rows,
  initialSort,
  searchAccessor,
  searchDebounceMs = 300,
}: UseSectionTableOptions<Row>) {
  const defaultKeys = useMemo(
    () => defaultColumnKeys ?? columns.map((c) => c.key),
    [defaultColumnKeys, columns],
  )
  const { columns: visibleColumns, selectedKeys, toggleColumn, moveColumn, options, pinnedKeys: pinned } =
    useVisibleTableColumns(storageKey, columns, defaultKeys, pinnedKeys)

  const columnSettings: ColumnSettingsProps = {
    options,
    value: selectedKeys,
    pinnedKeys: pinned,
    onToggle: toggleColumn,
    onMove: moveColumn,
  }

  const [sort, setSort] = useState<SortState | undefined>(initialSort)
  const toggleSort = (key: string) =>
    setSort((current) =>
      current?.key === key
        ? { key, dir: current.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'asc' },
    )

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(searchInput.trim().toLowerCase()), searchDebounceMs)
    return () => window.clearTimeout(timer)
  }, [searchInput, searchDebounceMs])

  const processedRows = useMemo(() => {
    let next = rows
    if (searchAccessor && search) {
      next = next.filter((row) => searchAccessor(row).toLowerCase().includes(search))
    }
    if (sort) {
      next = [...next].sort((a, b) =>
        compareCells(
          (a as Record<string, unknown>)[sort.key],
          (b as Record<string, unknown>)[sort.key],
          sort.dir,
        ),
      )
    }
    return next
  }, [rows, searchAccessor, search, sort])

  return {
    visibleColumns,
    columnSettings,
    sort,
    toggleSort,
    searchInput,
    setSearchInput,
    search,
    rows: processedRows,
  }
}
