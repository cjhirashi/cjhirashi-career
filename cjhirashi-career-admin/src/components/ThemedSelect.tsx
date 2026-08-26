import React, { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Check, ChevronDown, Plus } from 'lucide-react'
import { clsx } from 'clsx'
import { SelectOption } from '@/config/careerResources'
import { SelectCapsule, SelectOptionIdentity } from '@/components/SelectCapsule'
import { PersonChip } from '@/components/PersonAvatar'

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
  /**
   * Allow typing a value that is not yet in `options`. Used for categorical
   * columns whose vocabulary grows as Carlos saves records.
   */
  creatable?: boolean
}

interface SelectRow extends SelectOption {
  isCreate?: boolean
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
  creatable = false,
}) => {
  const autoId = useId()
  const listboxId = `${id ?? autoId}-listbox`
  const [open, setOpen] = useState(false)
  const [highlighted, setHighlighted] = useState(0)
  const [query, setQuery] = useState('')
  const searchRef = useRef<HTMLInputElement>(null)
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([])

  const listedOptions = useMemo<SelectOption[]>(() => {
    if (value && !options.some((opt) => opt.value === value)) {
      return [{ value, label: value }, ...options]
    }
    return options
  }, [options, value])

  const selected = listedOptions.find((opt) => opt.value === value)
  const showSearch = creatable || listedOptions.length >= 8

  const rows = useMemo<SelectRow[]>(() => {
    const q = query.trim().toLowerCase()
    const filtered = q
      ? listedOptions.filter(
          (opt) => opt.label.toLowerCase().includes(q) || opt.value.toLowerCase().includes(q)
        )
      : listedOptions
    const next: SelectRow[] = allowEmpty ? [{ value: '', label: placeholder }, ...filtered] : [...filtered]
    if (creatable) {
      const typed = query.trim()
      const exists = listedOptions.some(
        (opt) => opt.value.toLowerCase() === typed.toLowerCase() || opt.label.toLowerCase() === typed.toLowerCase()
      )
      if (typed && !exists) {
        next.push({ value: typed, label: `Añadir «${typed}»`, isCreate: true })
      }
    }
    return next
  }, [listedOptions, query, placeholder, allowEmpty, creatable])

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
    const selectedIndex = rows.findIndex((opt) => opt.value === value && !opt.isCreate)
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

  const commitTypedOrHighlighted = () => {
    const typed = query.trim()
    if (creatable && typed) {
      const match = listedOptions.find(
        (opt) => opt.value.toLowerCase() === typed.toLowerCase() || opt.label.toLowerCase() === typed.toLowerCase()
      )
      pick(match ? match.value : typed)
      return
    }
    const option = rows[highlighted]
    if (option) pick(option.value)
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
      commitTypedOrHighlighted()
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
        {listedOptions.map((opt) => (
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
        {selected ? (
          <span className="min-w-0 flex-1">
            {'imageUrl' in selected ? (
              <PersonChip src={selected.imageUrl} name={selected.label} size={22} />
            ) : (
              <SelectCapsule code={selected.value} label={selected.label} />
            )}
          </span>
        ) : (
          <span className="min-w-0 truncate">{placeholder}</span>
        )}
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
                  placeholder={creatable ? 'Escribe para filtrar o añadir…' : 'Filtrar…'}
                  className="input-field py-1.5 text-sm"
                  aria-label={creatable ? 'Filtrar o añadir opción' : 'Filtrar opciones'}
                />
              </div>
            )}

            {rows.length === 0 && query.trim() !== '' && (
              <p className="px-3 py-2 text-sm text-text-muted">Sin coincidencias</p>
            )}

            {rows.length === 0 && query.trim() === '' && creatable && (
              <p className="px-3 py-2 text-sm text-text-muted">Sin opciones aún. Escribe para añadir una.</p>
            )}

            {rows.map((opt, index) => {
              const isSelected = !opt.isCreate && opt.value === value
              const isPlaceholder = opt.value === '' && !opt.isCreate
              return (
                <button
                  key={opt.isCreate ? '__create__' : opt.value || '__empty__'}
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
                  {opt.isCreate ? (
                    <span className="min-w-0 flex items-center gap-2 text-primary">
                      <Plus size={14} className="flex-shrink-0" aria-hidden="true" />
                      <span className="min-w-0 truncate">{opt.label}</span>
                    </span>
                  ) : 'imageUrl' in opt ? (
                    <PersonChip src={opt.imageUrl} name={opt.label} size={22} />
                  ) : (
                    <SelectOptionIdentity
                      code={isPlaceholder ? undefined : opt.value}
                      label={opt.label}
                      muted={isPlaceholder}
                    />
                  )}
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
