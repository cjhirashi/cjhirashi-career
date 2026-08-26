import React from 'react'
import { useColumnOptions } from '@/hooks/useColumnOptions'
import { ThemedSelect } from '@/components/ThemedSelect'

interface CreatableSelectFieldProps {
  id: string
  name: string
  resource: string
  field: string
  value: string
  onChange: (value: string) => void
  required?: boolean
  placeholder?: string
}

/**
 * Categorical select whose options are the distinct values already stored
 * in this column. Carlos can type a new option; once the record is saved,
 * that value appears in the list for every later record.
 */
export const CreatableSelectField: React.FC<CreatableSelectFieldProps> = ({
  id,
  name,
  resource,
  field,
  value,
  onChange,
  required,
  placeholder,
}) => {
  const { options, isLoading } = useColumnOptions(resource, field)

  if (isLoading) {
    return (
      <div className="input-field flex items-center gap-2 text-text-secondary text-sm">
        <span className="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full" />
        Cargando opciones…
      </div>
    )
  }

  return (
    <ThemedSelect
      id={id}
      name={name}
      value={value}
      onChange={onChange}
      options={options}
      required={required}
      placeholder={placeholder ?? '— Escribe o selecciona —'}
      allowEmpty={!required}
      creatable
    />
  )
}
