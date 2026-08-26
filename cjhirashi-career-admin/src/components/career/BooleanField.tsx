import React from 'react'
import { ThemedSwitch } from '@/components/ThemedSwitch'

interface BooleanFieldProps {
  id: string
  name?: string
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  helpText?: string
}

/**
 * Form row for a boolean: title + help on the left, animated switch on the right.
 * Reads as a settings control, not as a checkbox with a trailing label.
 */
export const BooleanField: React.FC<BooleanFieldProps> = ({
  id,
  name,
  label,
  checked,
  onChange,
  helpText,
}) => (
  <div className="boolean-field" data-on={checked ? 'true' : 'false'}>
    <div className="boolean-field-copy">
      <label htmlFor={id} className="boolean-field-title">
        {label}
      </label>
      {helpText && <p className="boolean-field-help">{helpText}</p>}
    </div>
    <div className="boolean-field-control">
      <span className="boolean-field-state" aria-hidden="true">
        {checked ? 'Activo' : 'Inactivo'}
      </span>
      <ThemedSwitch id={id} name={name} checked={checked} onChange={onChange} aria-label={label} />
    </div>
  </div>
)
