import React from 'react'
import { FieldConfig, SelectOption } from '@/config/careerResources'
import { ListFilters } from '@/api/career'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'
import { useColumnOptions } from '@/hooks/useColumnOptions'
import { useFkOptions } from '@/hooks/useFkOptions'
import { FILTERABLE_FIELD_TYPES, NON_COLUMN_FILTER_FIELDS } from '@/utils/listFilters'

const BOOLEAN_OPTIONS: SelectOption[] = [
  { value: 'true', label: 'Activo' },
  { value: 'false', label: 'Inactivo' },
]

export const isFilterableField = (field?: FieldConfig): field is FieldConfig =>
  Boolean(
    field &&
      (FILTERABLE_FIELD_TYPES as readonly string[]).includes(field.type) &&
      !NON_COLUMN_FILTER_FIELDS.has(field.name)
  )

const selectedValues = (raw: ListFilters[string] | undefined): string[] => {
  if (Array.isArray(raw)) return raw.map(String)
  if (raw === true || raw === false) return [String(raw)]
  if (raw == null || raw === '') return []
  return [String(raw)]
}

const setFilter = (current: ListFilters, name: string, next: string[]): ListFilters => {
  const copy = { ...current }
  if (next.length === 0) delete copy[name]
  else copy[name] = next
  return copy
}

export const ColumnFilterButton: React.FC<{
  resourceKey: string
  field: FieldConfig
  value: ListFilters
  onChange: (next: ListFilters) => void
}> = ({ resourceKey, field, value, onChange }) => {
  const fk = useFkOptions(
    field.type === 'fk-select' || field.type === 'fk-multi-select' ? field.fkResource : undefined,
    field.fkLabelField,
    field.fkApi ?? 'career'
  )
  const distinct = useColumnOptions(
    field.type === 'creatable-select' ? resourceKey : '',
    field.type === 'creatable-select' ? field.name : ''
  )

  const options: SelectOption[] =
    field.type === 'boolean'
      ? BOOLEAN_OPTIONS
      : field.type === 'creatable-select'
        ? distinct.options
        : field.type === 'fk-select' || field.type === 'fk-multi-select'
          ? fk.options
          : (field.options ?? [])

  return (
    <ThemedMultiSelect
      variant="icon"
      aria-label={field.label}
      value={selectedValues(value[field.name])}
      onChange={(next) => onChange(setFilter(value, field.name, next))}
      options={options}
    />
  )
}
