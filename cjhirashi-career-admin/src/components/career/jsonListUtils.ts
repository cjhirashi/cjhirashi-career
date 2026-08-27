import { JsonListConfig, JsonListItemField } from '@/config/careerResources'

export type JsonListRow = Record<string, string>

const KV_NAME = 'name'
const KV_VALUE = 'value'
const TEXT_KEY = 'text'

export const defaultJsonList = (): JsonListConfig => ({
  kind: 'kv',
  itemNoun: 'dato',
  addLabel: 'Añadir dato',
  keyLabel: 'Nombre',
  valueLabel: 'Valor',
})

export const jsonListConfigOf = (config?: JsonListConfig): JsonListConfig => config ?? defaultJsonList()

const asString = (value: unknown): string => {
  if (value == null) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return ''
}

const blankRecord = (fields: JsonListItemField[]): JsonListRow => {
  const row: JsonListRow = {}
  for (const field of fields) row[field.name] = ''
  return row
}

export const blankJsonListRow = (config: JsonListConfig): JsonListRow => {
  if (config.kind === 'kv') return { [KV_NAME]: '', [KV_VALUE]: '' }
  if (config.kind === 'text') return { [TEXT_KEY]: '' }
  return blankRecord(config.itemFields ?? [])
}

const kvFromUnknown = (item: unknown): JsonListRow => {
  if (typeof item === 'string') return { [KV_NAME]: '', [KV_VALUE]: item }
  if (item && typeof item === 'object' && !Array.isArray(item)) {
    const rec = item as Record<string, unknown>
    if ('name' in rec || 'label' in rec || 'key' in rec || 'value' in rec) {
      return {
        [KV_NAME]: asString(rec.name ?? rec.label ?? rec.key),
        [KV_VALUE]: asString(rec.value ?? rec.detail ?? rec.text),
      }
    }
    const entries = Object.entries(rec)
    if (entries.length === 1) {
      return { [KV_NAME]: entries[0][0], [KV_VALUE]: asString(entries[0][1]) }
    }
  }
  return { [KV_NAME]: '', [KV_VALUE]: asString(item) }
}

const recordFromUnknown = (item: unknown, fields: JsonListItemField[]): JsonListRow => {
  const row = blankRecord(fields)
  if (typeof item === 'string') {
    if (fields[0]) row[fields[0].name] = item
    return row
  }
  if (item && typeof item === 'object' && !Array.isArray(item)) {
    const rec = item as Record<string, unknown>
    for (const field of fields) row[field.name] = asString(rec[field.name])
  }
  return row
}

/** API JSONB → editor rows (always an array of string maps). */
export const toEditorRows = (apiValue: unknown, config: JsonListConfig): JsonListRow[] => {
  if (apiValue == null || apiValue === '') return []

  if (config.kind === 'kv') {
    if (typeof apiValue === 'string') return [{ [KV_NAME]: '', [KV_VALUE]: apiValue }]
    if (Array.isArray(apiValue)) return apiValue.map(kvFromUnknown)
    if (typeof apiValue === 'object') {
      return Object.entries(apiValue as Record<string, unknown>).map(([name, value]) => ({
        [KV_NAME]: name,
        [KV_VALUE]: asString(value),
      }))
    }
    return []
  }

  if (config.kind === 'text') {
    if (typeof apiValue === 'string') return apiValue.trim() ? [{ [TEXT_KEY]: apiValue }] : []
    if (Array.isArray(apiValue)) {
      return apiValue.map((item) => ({
        [TEXT_KEY]: typeof item === 'string' ? item : asString(item),
      }))
    }
    if (typeof apiValue === 'object') {
      return Object.values(apiValue as Record<string, unknown>).map((item) => ({
        [TEXT_KEY]: asString(item),
      }))
    }
    return []
  }

  const fields = config.itemFields ?? []
  if (Array.isArray(apiValue)) return apiValue.map((item) => recordFromUnknown(item, fields))
  if (typeof apiValue === 'object') return [recordFromUnknown(apiValue, fields)]
  if (typeof apiValue === 'string' && apiValue.trim()) return [recordFromUnknown(apiValue, fields)]
  return []
}

const isRowEmpty = (row: JsonListRow, config: JsonListConfig): boolean => {
  if (config.kind === 'kv') return !row[KV_NAME]?.trim() && !row[KV_VALUE]?.trim()
  if (config.kind === 'text') return !row[TEXT_KEY]?.trim()
  return (config.itemFields ?? []).every((field) => !row[field.name]?.trim())
}

/** Editor rows → JSONB payload (object, string[], object[], or null). */
export const toApiValue = (rows: JsonListRow[], config: JsonListConfig): unknown => {
  const filled = rows.filter((row) => !isRowEmpty(row, config))
  if (filled.length === 0) return null

  if (config.kind === 'kv') {
    const obj: Record<string, string> = {}
    let unnamed = 0
    for (const row of filled) {
      const value = (row[KV_VALUE] ?? '').trim()
      const name = (row[KV_NAME] ?? '').trim()
      if (name) obj[name] = value
      else {
        unnamed += 1
        obj[`Dato ${unnamed}`] = value
      }
    }
    return obj
  }

  if (config.kind === 'text') {
    return filled.map((row) => row[TEXT_KEY].trim())
  }

  const fields = config.itemFields ?? []
  return filled.map((row) => {
    const item: Record<string, string> = {}
    for (const field of fields) {
      const value = (row[field.name] ?? '').trim()
      if (value) item[field.name] = value
    }
    return item
  })
}

export const parseEditorRows = (raw: string, config: JsonListConfig): JsonListRow[] => {
  if (!raw.trim()) return []
  try {
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return toEditorRows(parsed, config)
    return parsed.map((item) => {
      if (item && typeof item === 'object' && !Array.isArray(item)) {
        const rec = item as Record<string, unknown>
        const row: JsonListRow = {}
        for (const [key, value] of Object.entries(rec)) row[key] = asString(value)
        return row
      }
      return blankJsonListRow(config)
    })
  } catch {
    return []
  }
}

export const countJsonList = (apiValue: unknown, config: JsonListConfig): number =>
  toEditorRows(apiValue, config).filter((row) => !isRowEmpty(row, config)).length

export const summarizeJsonList = (apiValue: unknown, config: JsonListConfig): string => {
  const count = countJsonList(apiValue, config)
  if (count === 0) return '—'
  const noun = config.itemNoun
  if (count === 1) return `1 ${noun}`
  const plural =
    noun.endsWith('n') || noun.endsWith('r') || noun.endsWith('l') ? `${noun}es` : `${noun}s`
  return `${count} ${plural}`
}

export const isJsonListEmpty = (apiValue: unknown): boolean => {
  if (apiValue == null || apiValue === '') return true
  if (Array.isArray(apiValue)) return apiValue.length === 0
  if (typeof apiValue === 'object') return Object.keys(apiValue as object).length === 0
  return false
}
