import React, { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { clsx } from 'clsx'
import { SelectOption } from '@/config/careerResources'

export interface ThemedSelectProps {
  id?: string
  name?: string
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  required?: boolean
  disabled?: boolean
  className?: string
  'aria-label'?: string
  /** When false, the empty placeholder is not a selectable row (status pickers). */
  allowEmpty?: boolean
}

/**
 * Theme-aware select. Native `<option>` lists are painted by the OS, so they
 * ignore Glass Steel tokens (white popup in dark mode). This button+popover
 * uses `--bg-popover` / `--text-primary` like the navbar user menu.
 */
export const ThemedSelect: React.FC<ThemedSelectProps> = ({
  id,
  name,
  value,
  onChange,
  options,
  placeholder = '-- Selecciona --',
  required,
  disabled,
  className,
  'aria-label': ariaLabel,
  allowEmpty = true,
}) => {
  const autoId = useId()
  const listboxId = `${id ?? autoId}-listbox`
  const [open, setOpen] = useState(false)
  const [highlighted, setHighlighted] = useState(0)
  const [query, setQuery] = useState('')
  const searchRef = useRef<HTMLInputElement>(null)
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([])

  const selected = options.find((opt) => opt.value === value)
  const label = selected?.label ?? placeholder
  const showSearch = options.length >= 8

  const rows = useMemo<SelectOption[]>(() => {
    const q = query.trim().toLowerCase()
    const filtered = q
      ? options.filter(
          (opt) => opt.label.toLowerCase().includes(q) || opt.value.toLowerCase().includes(q)
        )
      : options
    return allowEmpty ? [{ value: '', label: placeholder }, ...filtered] : filtered
  }, [options, query, placeholder, allowEmpty])

  const close = () => {
    setOpen(false)
    setQuery('')
  }

  const pick = (next: string) => {
    onChange(next)
    close()
  }

  useEffect(() => {
    if (!open) return
    const selectedIndex = rows.findIndex((opt) => opt.value === value)
    setHighlighted(selectedIndex >= 0 ? selectedIndex : 0)
    const timer = window.setTimeout(() => {
      if (showSearch) searchRef.current?.focus()
      else optionRefs.current[selectedIndex >= 0 ? selectedIndex : 0]?.focus()
    }, 0)
    return () => window.clearTimeout(timer)
    // Only when the menu opens: re-running on `rows` would steal focus from the filter input.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  useEffect(() => {
    optionRefs.current[highlighted]?.scrollIntoView({ block: 'nearest' })
  }, [highlighted])

  const moveHighlight = (delta: number) => {
    if (rows.length === 0) return
    setHighlighted((current) => {
      const next = (current + delta + rows.length) % rows.length
      optionRefs.current[next]?.focus()
      return next
    })
  }

  const handleTriggerKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return
    if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      setOpen(true)
    }
  }

  const handleListKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault()
      close()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      moveHighlight(1)
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      moveHighlight(-1)
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      const option = rows[highlighted]
      if (option) pick(option.value)
    }
  }

  return (
    <div className={clsx('relative', className)}>
      {/* Keeps HTML5 `required` working on ResourceForm submit. */}
      <select
        name={name}
        value={value}
        required={required}
        disabled={disabled}
        tabIndex={-1}
        aria-hidden="true"
        className="sr-only"
        onChange={(e) => onChange(e.target.value)}
      >
        {allowEmpty && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <button
        type="button"
        id={id}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-label={ariaLabel}
        aria-required={required}
        onClick={() => (open ? close() : setOpen(true))}
        onKeyDown={handleTriggerKeyDown}
        className={clsx(
          'input-field flex items-center justify-between gap-2 text-left cursor-pointer',
          !selected && 'text-text-muted'
        )}
      >
        <span className="min-w-0 truncate">{label}</span>
        <ChevronDown
          size={16}
          className={clsx('flex-shrink-0 text-text-secondary transition-transform', open && 'rotate-180')}
          aria-hidden="true"
        />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={close} />
          <div
            id={listboxId}
            role="listbox"
            aria-label={ariaLabel ?? placeholder}
            className="popover-menu absolute left-0 right-0 mt-1 z-50 max-h-60 overflow-y-auto py-1"
            onKeyDown={handleListKeyDown}
          >
            {showSearch && (
              <div className="px-2 pb-1">
                <input
                  ref={searchRef}
                  type="text"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value)
                    setHighlighted(0)
                  }}
                  placeholder="Filtrar…"
                  className="input-field py-1.5 text-sm"
                  aria-label="Filtrar opciones"
                />
              </div>
            )}

            {rows.length === 0 && query.trim() !== '' && (
              <p className="px-3 py-2 text-sm text-text-muted">Sin coincidencias</p>
            )}

            {rows.map((opt, index) => {
              const isSelected = opt.value === value
              const isPlaceholder = opt.value === ''
              return (
                <button
                  key={opt.value || '__empty__'}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  ref={(el) => {
                    optionRefs.current[index] = el
                  }}
                  className="popover-menu-item"
                  data-highlighted={index === highlighted ? 'true' : undefined}
                  onMouseEnter={() => setHighlighted(index)}
                  onClick={() => pick(opt.value)}
                >
                  <span className={clsx('min-w-0 truncate', isPlaceholder && 'text-text-muted')}>
                    {opt.label}
                  </span>
                  {isSelected && !isPlaceholder && (
                    <Check size={14} className="text-primary flex-shrink-0" aria-hidden="true" />
                  )}
                </button>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
