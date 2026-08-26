import React from 'react'
import { clsx } from 'clsx'

export interface ThemedSwitchProps {
  id?: string
  name?: string
  checked: boolean
  onChange?: (checked: boolean) => void
  disabled?: boolean
  className?: string
  'aria-label': string
}

/**
 * Two-state animated switch. The field title lives outside this control
 * (`BooleanField`) so the form row can be composed like other inputs.
 */
export const ThemedSwitch: React.FC<ThemedSwitchProps> = ({
  id,
  name,
  checked,
  onChange,
  disabled = false,
  className,
  'aria-label': ariaLabel,
}) => {
  return (
    <button
      type="button"
      id={id}
      role="switch"
      name={name}
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      onClick={() => {
        if (disabled || !onChange) return
        onChange(!checked)
      }}
      className={clsx('themed-switch', className)}
      data-on={checked ? 'true' : 'false'}
    >
      <span className="themed-switch-knob" aria-hidden="true" />
    </button>
  )
}
