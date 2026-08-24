import React from 'react'
import { useFkOptions } from '@/hooks/useFkOptions'

interface FkSelectFieldProps {
  id: string
  name: string
  fkResource: string
  fkLabelField?: string | string[]
  value: string
  onChange: (value: string) => void
  required?: boolean
  placeholder?: string
}

/**
 * A <select> that loads its options from a career resource.
 * Each option shows "id — Name" so the user knows exactly what
 * record they are linking to.
 */
export const FkSelectField: React.FC<FkSelectFieldProps> = ({
  id,
  name,
  fkResource,
  fkLabelField,
  value,
  onChange,
  required,
  placeholder,
}) => {
  const { options, isLoading, isError } = useFkOptions(fkResource, fkLabelField)

  if (isLoading) {
    return (
      <div className="input-field flex items-center gap-2 text-text-secondary text-sm">
        <span className="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full" />
        Cargando opciones…
      </div>
    )
  }

  if (isError) {
    return (
      <div className="input-field text-red-500 text-sm">
        Error al cargar opciones de {fkResource}
      </div>
    )
  }

  return (
    <select
      id={id}
      name={name}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={required}
      className="input-field"
    >
      <option value="">{placeholder ?? '— Selecciona un registro —'}</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
