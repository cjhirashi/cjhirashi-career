import React, { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Check, ChevronDown, Filter, Plus, type LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import { SelectOption } from '@/config/careerResources'
import { SelectCapsule, SelectOptionIdentity } from '@/components/SelectCapsule'

interface MultiSelectRow extends SelectOption {
  isCreate?: boolean
}

export interface ThemedMultiSelectProps {
  id?: string
  name?: string
  value: string[]
  onChange: (value: string[]) => void
  options: SelectOption[]
  placeholder?: string
  required?: boolean
  disabled?: boolean
  className?: string
  'aria-label'?: string
  /** `icon`: compact filter button for column/field titles. */
  variant?: 'field' | 'icon'
  icon?: LucideIcon
  /** Overrides the default `Filtrar {aria-label}` on the icon trigger. */
  triggerLabel?: string
  align?: 'start' | 'end'
  showCount?: boolean
  triggerClassName?: string
  iconSize?: number
  /**
   * Allow typing a value that is not yet in `options` - same idea as
   * `ThemedSelect`'s `creatable`, but adding to the selection instead of
   * replacing a single value. Used by projects.competency_ids so a new
   * technology name gets created as a real record on save.
   */
  creatable?: boolean
}

const parseValues = (value: string[]): string[] =>
  value.map((item) => item.trim()).filter(Boolean)

const POPOVER_WIDTH = 256

/**
 * Theme-aware multi-select. Same Glass Steel popover as `ThemedSelect`
 * (`--bg-popover` / `--text-primary`); clicking an option toggles it and
 * keeps the menu open.
 */
export const ThemedMultiSelect: React.FC<ThemedMultiSelectProps> = ({
  id,
  name,
  value,
  onChange,
  options,
  placeholder = '— Selecciona —',
  required,
  disabled,
  className,
  'aria-label': ariaLabel,
  variant = 'field',
  icon: TriggerIcon = Filter,
  triggerLabel,
  align = 'start',
  showCount = true,
  triggerClassName,
  iconSize = 13,
  creatable = false,
}) => {
  const autoId = useId()
  const listboxId = `${id ?? autoId}-listbox`
  const selectedIds = useMemo(() => parseValues(value), [value])
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds])
  const [open, setOpen] = useState(false)
  const [highlighted, setHighlighted] = useState(0)
  const [query, setQuery] = useState('')
  const [popoverPos, setPopoverPos] = useState<{ top?: number; bottom?: number; left: number }>({ left: 0 })
  const searchRef = useRef<HTMLInputElement>(null)
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([])
  const triggerRef = useRef<HTMLElement | null>(null)
  const isIcon = variant === 'icon'

  // In creatable mode a selected id may be a freshly typed name with no
  // matching record yet (see FieldConfig.creatable) - synthesize a
  // pseudo-option so its capsule doesn't just disappear before save.
  const selectedOptions = useMemo(() => {
    const known = options.filter((opt) => selectedSet.has(opt.value))
    if (!creatable) return known
    const knownIds = new Set(known.map((opt) => opt.value))
    const pending = selectedIds
      .filter((id) => !knownIds.has(id))
      .map((id) => ({ value: id, label: id }))
    return [...known, ...pending]
  }, [options, selectedSet, selectedIds, creatable])
  const showSearch = creatable || options.length >= 8

  const rows = useMemo<MultiSelectRow[]>(() => {
    const q = query.trim().toLowerCase()
    const filtered = q
      ? options.filter(
          (opt) => opt.label.toLowerCase().includes(q) || opt.value.toLowerCase().includes(q)
        )
      : options
    if (!creatable) return filtered
    const typed = query.trim()
    const exists = options.some(
      (opt) => opt.value.toLowerCase() === typed.toLowerCase() || opt.label.toLowerCase() === typed.toLowerCase()
    )
    if (typed && !exists) {
      return [...filtered, { value: typed, label: `Añadir «${typed}»`, isCreate: true }]
    }
    return filtered
  }, [options, query, creatable])

  const close = () => {
    setOpen(false)
    setQuery('')
  }

  const toggle = (optionValue: string) => {
    if (!optionValue) return
    if (selectedSet.has(optionValue)) {
      onChange(selectedIds.filter((item) => item !== optionValue))
      return
    }
    onChange([...selectedIds, optionValue])
  }

  useLayoutEffect(() => {
    if (!open || !isIcon || !triggerRef.current) return
    const update = () => {
      const rect = triggerRef.current!.getBoundingClientRect()
      const spaceBelow = window.innerHeight - rect.bottom
      const openUp = spaceBelow < 260 && rect.top > 260
      const preferredLeft = align === 'end' ? rect.right - POPOVER_WIDTH : rect.left
      const left = Math.max(8, Math.min(preferredLeft, window.innerWidth - POPOVER_WIDTH - 8))
      setPopoverPos(
        openUp
          ? { bottom: window.innerHeight - rect.top + 4, left }
          : { top: rect.bottom + 4, left }
      )
    }
    update()
    window.addEventListener('scroll', update, true)
    window.addEventListener('resize', update)
    return () => {
      window.removeEventListener('scroll', update, true)
      window.removeEventListener('resize', update)
    }
  }, [open, isIcon, align])

  useEffect(() => {
    if (!open) return
    const timer = window.setTimeout(() => {
      if (showSearch) searchRef.current?.focus()
      else optionRefs.current[0]?.focus()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [open, showSearch])

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
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      const option = rows[highlighted]
      if (option) toggle(option.value)
    }
  }

  const filterLabel = triggerLabel ?? (ariaLabel ? `Filtrar ${ariaLabel}` : 'Filtrar')

  const listbox = open ? (
    <div
      id={listboxId}
      role="listbox"
      aria-multiselectable="true"
      aria-label={ariaLabel ?? placeholder}
      className={clsx(
        'popover-menu max-h-60 overflow-y-auto py-1',
        isIcon ? 'z-[60]' : 'absolute left-0 right-0 mt-1 z-50'
      )}
      style={
        isIcon
          ? {
              position: 'fixed',
              top: popoverPos.top,
              bottom: popoverPos.bottom,
              left: popoverPos.left,
              width: POPOVER_WIDTH,
            }
          : undefined
      }
      onKeyDown={handleListKeyDown}
      onClick={(e) => e.stopPropagation()}
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

      {rows.length === 0 && query.trim() === '' && (
        <p className="px-3 py-2 text-sm text-text-muted">
          {creatable ? 'Sin opciones aún. Escribe para añadir una.' : 'No hay opciones'}
        </p>
      )}

      {rows.map((opt, index) => {
        const isSelected = !opt.isCreate && selectedSet.has(opt.value)
        return (
          <button
            key={opt.isCreate ? '__create__' : opt.value}
            type="button"
            role="option"
            aria-selected={isSelected}
            ref={(el) => {
              optionRefs.current[index] = el
            }}
            className="popover-menu-item"
            data-highlighted={index === highlighted ? 'true' : undefined}
            onMouseEnter={() => setHighlighted(index)}
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              toggle(opt.value)
              if (opt.isCreate) setQuery('')
            }}
          >
            {opt.isCreate ? (
              <span className="min-w-0 flex items-center gap-2 text-primary">
                <Plus size={14} className="flex-shrink-0" aria-hidden="true" />
                <span className="min-w-0 truncate">{opt.label}</span>
              </span>
            ) : (
              <SelectOptionIdentity code={opt.value} label={opt.label} />
            )}
            {isSelected && <Check size={14} className="text-primary flex-shrink-0" aria-hidden="true" />}
          </button>
        )
      })}
    </div>
  ) : null

  const overlay = open ? (
    <div
      className={clsx('fixed inset-0', isIcon ? 'z-[55]' : 'z-40')}
      onClick={close}
    />
  ) : null

  return (
    <div className={clsx('relative', isIcon ? 'inline-flex' : undefined, className)}>
      {name &&
        selectedIds.map((item) => (
          <input key={item} type="hidden" name={name} value={item} />
        ))}
      {name && required && selectedIds.length === 0 && (
        <input type="hidden" name={name} value="" required />
      )}

      {isIcon ? (
        <button
          ref={(el) => {
            triggerRef.current = el
          }}
          type="button"
          id={id}
          role="combobox"
          aria-disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-label={filterLabel}
          aria-required={required}
          aria-multiselectable="true"
          disabled={disabled}
          data-active={showCount && selectedIds.length > 0 ? 'true' : undefined}
          className={clsx(triggerClassName ?? 'column-filter-btn')}
          title={filterLabel}
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            if (disabled) return
            open ? close() : setOpen(true)
          }}
          onKeyDown={handleTriggerKeyDown}
        >
          <TriggerIcon size={iconSize} aria-hidden="true" />
          {showCount && selectedIds.length > 0 && (
            <span className="column-filter-count">{selectedIds.length}</span>
          )}
        </button>
      ) : (
        <div
          ref={(el) => {
            triggerRef.current = el
          }}
          id={id}
          role="combobox"
          tabIndex={disabled ? -1 : 0}
          aria-disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-label={ariaLabel}
          aria-required={required}
          aria-multiselectable="true"
          onClick={() => {
            if (disabled) return
            open ? close() : setOpen(true)
          }}
          onKeyDown={handleTriggerKeyDown}
          className={clsx(
            'input-field flex items-center justify-between gap-2 text-left cursor-pointer min-h-[2.5rem]',
            selectedOptions.length === 0 && 'text-text-muted',
            disabled && 'opacity-50 pointer-events-none'
          )}
        >
          <span className="min-w-0 flex-1 flex flex-wrap items-center gap-1">
            {selectedOptions.length === 0 ? (
              <span className="truncate">{placeholder}</span>
            ) : (
              selectedOptions.map((opt) => (
                <SelectCapsule
                  key={opt.value}
                  code={opt.value}
                  label={opt.label}
                  removeLabel={`Quitar ${opt.label}`}
                  onRemove={() => toggle(opt.value)}
                />
              ))
            )}
          </span>
          <ChevronDown
            size={16}
            className={clsx('flex-shrink-0 text-text-secondary transition-transform', open && 'rotate-180')}
            aria-hidden="true"
          />
        </div>
      )}

      {isIcon
        ? open &&
          createPortal(
            <>
              {overlay}
              {listbox}
            </>,
            document.body
          )
        : (
          <>
            {overlay}
            {listbox}
          </>
        )}
    </div>
  )
}
