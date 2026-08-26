import React from 'react'
import { X } from 'lucide-react'
import { clsx } from 'clsx'

export interface SelectCapsuleProps {
  /** Technical id / enum value shown in the left rail. */
  code?: string
  /** Human-readable name. */
  label: string
  onRemove?: () => void
  removeLabel?: string
}

/** If a legacy `"id — name"` label sneaks in, keep the name side clean. */
export function splitCodeAndName(code: string | undefined, label: string): { code?: string; name: string } {
  if (!code) return { name: label }
  const prefix = `${code} — `
  const name = label.startsWith(prefix) ? label.slice(prefix.length) : label
  if (name === code) return { name }
  return { code, name }
}

/**
 * Split identity chip: mono id rail + name. Used by themed select/multi-select
 * and by the record viewer for the same field types.
 */
export const SelectCapsule: React.FC<SelectCapsuleProps> = ({ code, label, onRemove, removeLabel }) => {
  const parts = splitCodeAndName(code, label)
  return (
    <span className="select-capsule" title={parts.code ? `${parts.code} · ${parts.name}` : parts.name}>
      {parts.code && (
        <span className="select-capsule-id" title={parts.code}>
          {parts.code}
        </span>
      )}
      <span className="select-capsule-name">{parts.name}</span>
      {onRemove && (
        <button
          type="button"
          aria-label={removeLabel ?? `Quitar ${parts.name}`}
          className="select-capsule-remove"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            onRemove()
          }}
        >
          <X size={11} aria-hidden="true" />
        </button>
      )}
    </span>
  )
}

export const SelectCapsuleGroup: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => <span className={clsx('flex flex-wrap items-center gap-1.5', className)}>{children}</span>

/** Dropdown row: id and name as two columns, same visual language as the capsule. */
export const SelectOptionIdentity: React.FC<{
  code?: string
  label: string
  muted?: boolean
}> = ({ code, label, muted }) => {
  const parts = splitCodeAndName(code, label)
  return (
    <span className={clsx('min-w-0 flex items-center gap-2', muted && 'text-text-muted')}>
      {parts.code && <span className="select-option-id">{parts.code}</span>}
      <span className="min-w-0 truncate">{parts.name}</span>
    </span>
  )
}
