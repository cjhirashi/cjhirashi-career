import { useCallback, useMemo, useState } from 'react'
import { ColumnConfig, SelectOption } from '@/config/careerResources'
import {
  columnStorageKey,
  ID_COLUMN,
  moveColumnKey,
  pinColumnOrder,
  readStoredColumnKeys,
  resolveVisibleColumns,
  toggleColumnKey,
} from '@/utils/tableColumns'

export function useVisibleTableColumns(
  resourceKey: string,
  available: ColumnConfig[],
  defaultKeys: string[],
  pinnedKeys: string[] = [ID_COLUMN.key]
) {
  const storageKey = columnStorageKey(resourceKey)
  const allowed = useMemo(() => new Set(available.map((col) => col.key)), [available])
  const pinned = useMemo(
    () => pinnedKeys.filter((key) => allowed.has(key)),
    [pinnedKeys, allowed]
  )
  const fallback = useMemo(
    () =>
      pinColumnOrder(
        defaultKeys.filter((key) => allowed.has(key)).length > 0 ? defaultKeys : [ID_COLUMN.key],
        pinned,
        allowed
      ),
    [defaultKeys, allowed, pinned]
  )

  const [selectedKeys, setSelectedKeys] = useState<string[]>(() =>
    pinColumnOrder(readStoredColumnKeys(storageKey, fallback, allowed), pinned, allowed)
  )

  const persist = useCallback(
    (next: string[]) => {
      const stored = pinColumnOrder(next, pinned, allowed)
      setSelectedKeys(stored)
      try {
        localStorage.setItem(storageKey, JSON.stringify(stored))
      } catch {
        /* private mode / quota */
      }
    },
    [allowed, pinned, storageKey]
  )

  const setVisible = useCallback(
    (next: string[]) => {
      persist(next)
    },
    [persist]
  )

  const toggleColumn = useCallback(
    (key: string) => {
      persist(toggleColumnKey(selectedKeys, key, pinned, allowed))
    },
    [allowed, persist, pinned, selectedKeys]
  )

  const moveColumn = useCallback(
    (key: string, direction: -1 | 1) => {
      persist(moveColumnKey(selectedKeys, key, direction, pinned, allowed))
    },
    [allowed, persist, pinned, selectedKeys]
  )

  const columns = useMemo(
    () => resolveVisibleColumns(available, selectedKeys, fallback, pinned),
    [available, selectedKeys, fallback, pinned]
  )

  const options = useMemo<SelectOption[]>(
    () => available.map((col) => ({ value: col.key, label: col.label })),
    [available]
  )

  return {
    columns,
    selectedKeys: columns.map((col) => col.key),
    setVisible,
    toggleColumn,
    moveColumn,
    pinnedKeys: pinned,
    options,
  }
}
