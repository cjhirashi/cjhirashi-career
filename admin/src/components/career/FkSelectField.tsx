import React from 'react'
import { useFkOptions, FkApiMode } from '@/hooks/useFkOptions'
import { ThemedSelect } from '@/components/ThemedSelect'

interface FkSelectFieldProps {
  id: string
  name: string
  fkResource: string
  fkLabelField?: string | string[]
  fkApi?: FkApiMode
  value: string
  onChange: (value: string) => void
  required?: boolean
  placeholder?: string
}

/**
 * A themed select that loads its options from a career resource.
 * Each option shows "id — Name" so the user knows exactly what
 * record they are linking to.
 */
export const FkSelectField: React.FC<FkSelectFieldProps> = ({
  id,
  name,
  fkResource,
  fkLabelField,
  fkApi = 'career',
  value,
  onChange,
  required,
  placeholder,
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
    return (
      <div className="input-field text-red-500 text-sm">
        Error al cargar opciones de {fkResource}
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
      placeholder={placeholder ?? '— Selecciona un registro —'}
    />
  )
}
