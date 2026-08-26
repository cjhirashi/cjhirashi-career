import { ColumnConfig, ColumnFormat, FieldConfig, ResourceConfig } from '@/config/careerResources'

export const ID_COLUMN: ColumnConfig = { key: 'id', label: 'ID' }

const NAME_FIELD_KEYS = ['name', 'title', 'original_filename', 'company', 'full_name', 'role_name', 'position_title']

const formatFromField = (type: FieldConfig['type']): ColumnFormat | undefined => {
  if (type === 'boolean') return 'boolean'
  if (type === 'date') return 'date'
  if (type === 'datetime') return 'datetime'
  if (type === 'number') return 'number'
  if (type === 'textarea' || type === 'code' || type === 'json') return 'truncate'
  return undefined
}

export const columnFromField = (field: FieldConfig): ColumnConfig => ({
  key: field.name,
  label: field.label,
  format: formatFromField(field.type),
})

/** The row's display name: first declared table column that is not `id`. */
export const nameColumnKey = (config: ResourceConfig): string | undefined => {
  const declared = config.columns.find((col) => col.key !== 'id')
  if (declared) return declared.key
  return config.fields.find((field) => NAME_FIELD_KEYS.includes(field.name))?.name
}

export const pinnedColumnKeys = (config: ResourceConfig): string[] => {
  const name = nameColumnKey(config)
  return name ? [ID_COLUMN.key, name] : [ID_COLUMN.key]
}

/** ID and name first; remaining keys keep the caller's order. */
export const pinColumnOrder = (keys: string[], pinned: string[], allowed: Set<string>): string[] => {
  const pinnedPresent = pinned.filter((key) => allowed.has(key))
  const pinnedSet = new Set(pinnedPresent)
  const rest = keys.filter((key) => allowed.has(key) && !pinnedSet.has(key))
  return [...pinnedPresent, ...rest]
}

/** Default visible columns: `id` plus the resource's declared table columns. */
export const defaultTableColumns = (config: ResourceConfig): ColumnConfig[] =>
  config.columns.some((col) => col.key === 'id') ? config.columns : [ID_COLUMN, ...config.columns]

/** Every attribute that can be shown: id, declared columns, then remaining form fields. */
export const availableTableColumns = (config: ResourceConfig): ColumnConfig[] => {
  const byKey = new Map<string, ColumnConfig>()
  byKey.set(ID_COLUMN.key, ID_COLUMN)
  for (const col of config.columns) byKey.set(col.key, col)
  for (const field of config.fields) {
    if (!byKey.has(field.name)) byKey.set(field.name, columnFromField(field))
  }
  return [...byKey.values()]
}

export const resolveVisibleColumns = (
  available: ColumnConfig[],
  selectedKeys: string[],
  fallbackKeys: string[],
  pinnedKeys: string[] = [ID_COLUMN.key]
): ColumnConfig[] => {
  const byKey = new Map(available.map((col) => [col.key, col]))
  const allowed = new Set(byKey.keys())
  const source = selectedKeys.length > 0 ? selectedKeys : fallbackKeys
  const ordered = pinColumnOrder(source, pinnedKeys, allowed)
  const cols = ordered.map((key) => byKey.get(key)).filter((col): col is ColumnConfig => Boolean(col))
  if (cols.length > 0) return cols
  return pinColumnOrder(fallbackKeys, pinnedKeys, allowed)
    .map((key) => byKey.get(key))
    .filter((col): col is ColumnConfig => Boolean(col))
}

export const toggleColumnKey = (
  keys: string[],
  key: string,
  pinned: string[],
  allowed: Set<string>
): string[] => {
  if (pinned.includes(key) || !allowed.has(key)) {
    return pinColumnOrder(keys, pinned, allowed)
  }
  if (keys.includes(key)) {
    return pinColumnOrder(
      keys.filter((item) => item !== key),
      pinned,
      allowed
    )
  }
  return pinColumnOrder([...keys, key], pinned, allowed)
}

export const moveColumnKey = (
  keys: string[],
  key: string,
  direction: -1 | 1,
  pinned: string[],
  allowed: Set<string>
): string[] => {
  const ordered = pinColumnOrder(keys, pinned, allowed)
  const pinnedSet = new Set(pinned.filter((item) => allowed.has(item)))
  const rest = ordered.filter((item) => !pinnedSet.has(item))
  const index = rest.indexOf(key)
  const nextIndex = index + direction
  if (index < 0 || nextIndex < 0 || nextIndex >= rest.length) return ordered
  const swapped = [...rest]
  ;[swapped[index], swapped[nextIndex]] = [swapped[nextIndex], swapped[index]]
  return [...ordered.filter((item) => pinnedSet.has(item)), ...swapped]
}

export const readStoredColumnKeys = (storageKey: string, fallback: string[], allowed: Set<string>): string[] => {
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return fallback
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return fallback
    const keys = parsed.filter((item): item is string => typeof item === 'string' && allowed.has(item))
    return keys.length > 0 ? keys : fallback
  } catch {
    return fallback
  }
}

export const columnStorageKey = (resourceKey: string) => `cjhirashi.career.table-columns.${resourceKey}`
