import { FieldConfig, FieldType } from '@/config/careerResources'
import { getAgentProfileLabel } from '@/config/agentProfiles'
import { formatDate, formatDateTime, truncate } from '@/utils/formatters'
import { jsonListConfigOf, parseEditorRows, summarizeJsonList, toApiValue, toEditorRows } from './jsonListUtils'

/**
 * Converts a raw API value into the string/boolean an <input>/<textarea>/
 * <select> needs for its `value`/`checked` prop.
 */
export const toFormValue = (
  type: FieldType,
  value: unknown,
  field?: FieldConfig
): string | boolean => {
  if (value === null || value === undefined) {
    return type === 'boolean' ? false : ''
  }

  switch (type) {
    case 'boolean':
      return Boolean(value)
    case 'date':
      // API returns "YYYY-MM-DD" already, but be defensive about datetimes.
      return typeof value === 'string' ? value.slice(0, 10) : ''
    case 'datetime':
      if (typeof value !== 'string') return ''
      // <input type="datetime-local"> needs "YYYY-MM-DDTHH:mm".
      return value.length >= 16 ? value.slice(0, 16) : value
    case 'string-array':
    case 'multi-select':
    case 'fk-multi-select':
      return Array.isArray(value) ? value.join('\n') : ''
    case 'number-array':
      return Array.isArray(value) ? value.join(', ') : ''
    case 'json':
      try {
        return JSON.stringify(toEditorRows(value, jsonListConfigOf(field?.jsonList)))
      } catch {
        return ''
      }
    case 'number':
      return typeof value === 'number' ? String(value) : ''
    case 'fk-select':
      return value != null ? String(value) : ''
    default:
      return typeof value === 'string' ? value : String(value)
  }
}

export class FieldParseError extends Error {
  constructor(public fieldLabel: string, message: string) {
    super(message)
    this.name = 'FieldParseError'
  }
}

/**
 * Converts a form's raw string/boolean value back into the JSON-serializable
 * value the API payload expects. Throws `FieldParseError` for malformed JSON
 * so the caller can surface a friendly message instead of a silent 422.
 */
export const fromFormValue = (field: FieldConfig, raw: string | boolean): unknown => {
  const { type, label } = field

  if (type === 'boolean') return Boolean(raw)

  const str = typeof raw === 'string' ? raw : String(raw)

  switch (type) {
    case 'number': {
      if (str.trim() === '') return null
      const n = Number(str)
      if (Number.isNaN(n)) throw new FieldParseError(label, `"${label}" debe ser un número`)
      return n
    }
    case 'date':
    case 'datetime':
      return str.trim() === '' ? null : str
    case 'string-array':
    case 'multi-select':
    case 'fk-multi-select':
      return str
        .split('\n')
        .map((s) => s.trim())
        .filter((s) => s.length > 0)
    case 'number-array': {
      const parts = str
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0)
      const numbers = parts.map(Number)
      if (numbers.some((n) => Number.isNaN(n))) {
        throw new FieldParseError(label, `"${label}" debe ser una lista de números separados por coma`)
      }
      return numbers
    }
    case 'json': {
      if (str.trim() === '') return null
      try {
        const config = jsonListConfigOf(field.jsonList)
        return toApiValue(parseEditorRows(str, config), config)
      } catch {
        throw new FieldParseError(label, `"${label}" no se pudo guardar. Revisa los registros.`)
      }
    }
    case 'fk-select':
      return str.trim() === '' ? null : str
    case 'code':
    case 'text':
    case 'textarea':
    default:
      return str.trim() === '' ? null : str
  }
}

/** Human-friendly rendering of a table cell value, driven by ColumnConfig.format. */
export const formatCellValue = (value: unknown, format?: string): string => {
  if (value === null || value === undefined || value === '') return '—'

  switch (format) {
    case 'date':
      return typeof value === 'string' ? formatDate(value) : String(value)
    case 'datetime':
      return typeof value === 'string' ? formatDateTime(value) : String(value)
    case 'boolean':
      return value ? 'Sí' : 'No'
    case 'truncate':
      return typeof value === 'string' ? truncate(value, 60) : String(value)
    case 'number':
      return String(value)
    case 'agents':
      if (!Array.isArray(value) || value.length === 0) return 'Todos'
      return value.map((id) => getAgentProfileLabel(String(id))).join(', ')
    default:
      if (Array.isArray(value) || (typeof value === 'object' && value !== null)) {
        return summarizeJsonList(value, jsonListConfigOf())
      }
      return String(value)
  }
}
