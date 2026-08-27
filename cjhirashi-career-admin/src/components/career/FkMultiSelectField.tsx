import React from 'react'
import { useFkOptions, FkApiMode } from '@/hooks/useFkOptions'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'

interface FkMultiSelectFieldProps {
  id: string
  name?: string
  fkResource: string
  fkLabelField?: string | string[]
  fkApi?: FkApiMode
  value: string
  onChange: (value: string) => void
  required?: boolean
  placeholder?: string
  /** Lets Carlos type a value not yet in `fkResource`'s options (see FieldConfig.creatable). */
  creatable?: boolean
}

const splitValues = (value: string): string[] =>
  value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)

/**
 * Themed multi-select of records from another career resource. The form
 * stores selected ids as a newline-separated string (same wire format as
 * `multi-select`); `fromFormValue` turns that into `string[]`.
 */
export const FkMultiSelectField: React.FC<FkMultiSelectFieldProps> = ({
  id,
  name,
  fkResource,
  fkLabelField,
  fkApi = 'career',
  value,
  onChange,
  required,
  placeholder,
  creatable = false,
}) => {
  const { options, isLoading, isError } = useFkOptions(fkResource, fkLabelField, fkApi)

  if (isLoading) {
    return (
      <div className="input-field flex items-center gap-2 text-text-secondary text-sm">
        <span className="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full" />
        Cargando opciones…
      </div>
    )
  }

  if (isError) {
    return <div className="input-field text-red-500 text-sm">Error al cargar opciones de {fkResource}</div>
  }

  return (
    <ThemedMultiSelect
      id={id}
      name={name}
      value={splitValues(value)}
      onChange={(ids) => onChange(ids.join('\n'))}
      options={options}
      required={required}
      placeholder={placeholder ?? '— Selecciona registros —'}
      creatable={creatable}
    />
  )
}
