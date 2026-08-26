import React, { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Check, ChevronDown, ChevronUp, Lock, Settings } from 'lucide-react'
import { SelectOption } from '@/config/careerResources'

interface TableColumnSettingsProps {
  options: SelectOption[]
  value: string[]
  pinnedKeys: string[]
  onToggle: (key: string) => void
  onMove: (key: string, direction: -1 | 1) => void
}

const POPOVER_WIDTH = 280

/** Gear in the table header: visibility + order of columns (ID/name pinned). */
export const TableColumnSettings: React.FC<TableColumnSettingsProps> = ({
  options,
  value,
  pinnedKeys,
  onToggle,
  onMove,
}) => {
  const autoId = useId()
  const listboxId = `${autoId}-columns`
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [popoverPos, setPopoverPos] = useState<{ top?: number; bottom?: number; left: number }>({ left: 0 })
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  const selectedSet = useMemo(() => new Set(value), [value])
  const pinnedSet = useMemo(() => new Set(pinnedKeys), [pinnedKeys])

  const byValue = useMemo(() => new Map(options.map((opt) => [opt.value, opt])), [options])

  const pinnedRows = pinnedKeys
    .map((key) => byValue.get(key))
    .filter((opt): opt is SelectOption => Boolean(opt))

  const visibleFlexible = value
    .filter((key) => !pinnedSet.has(key))
    .map((key) => byValue.get(key))
    .filter((opt): opt is SelectOption => Boolean(opt))

  const hiddenRows = options.filter((opt) => !selectedSet.has(opt.value) && !pinnedSet.has(opt.value))

  const q = query.trim().toLowerCase()
  const match = (opt: SelectOption) =>
    !q || opt.label.toLowerCase().includes(q) || opt.value.toLowerCase().includes(q)

  const close = () => {
    setOpen(false)
    setQuery('')
  }

  useLayoutEffect(() => {
    if (!open || !triggerRef.current) return
    const update = () => {
      const rect = triggerRef.current!.getBoundingClientRect()
      const spaceBelow = window.innerHeight - rect.bottom
      const openUp = spaceBelow < 320 && rect.top > 320
      const left = Math.max(8, Math.min(rect.left, window.innerWidth - POPOVER_WIDTH - 8))
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
  }, [open])

  useEffect(() => {
    if (!open) return
    const timer = window.setTimeout(() => searchRef.current?.focus(), 0)
    return () => window.clearTimeout(timer)
  }, [open])

  const showSearch = options.length >= 8

  return (
    <div className="relative inline-flex">
      <button
        ref={triggerRef}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-label="Columnas visibles"
        title="Columnas visibles"
        className="table-settings-btn"
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          open ? close() : setOpen(true)
        }}
      >
        <Settings size={15} aria-hidden="true" />
      </button>

      {open &&
        createPortal(
          <>
            <div className="fixed inset-0 z-[55]" onClick={close} />
            <div
              id={listboxId}
              role="listbox"
              aria-multiselectable="true"
              aria-label="Columnas visibles"
              className="popover-menu z-[60] max-h-80 overflow-y-auto py-1"
              style={{
                position: 'fixed',
                top: popoverPos.top,
                bottom: popoverPos.bottom,
                left: popoverPos.left,
                width: POPOVER_WIDTH,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {showSearch && (
                <div className="px-2 pb-1">
                  <input
                    ref={searchRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Buscar columna…"
                    className="input-field py-1.5 text-sm"
                    aria-label="Buscar columna"
                  />
                </div>
              )}

              {pinnedRows.filter(match).length > 0 && (
                <p className="px-3 pt-1 pb-0.5 text-[10px] uppercase tracking-wide text-text-muted">Fijas</p>
              )}
              {pinnedRows.filter(match).map((opt) => (
                <div key={opt.value} className="column-settings-row column-settings-row-pinned">
                  <Lock size={12} className="flex-shrink-0 text-text-muted" aria-hidden="true" />
                  <span className="min-w-0 flex-1 truncate text-sm">{opt.label}</span>
                  <Check size={14} className="text-primary flex-shrink-0" aria-hidden="true" />
                </div>
              ))}

              {visibleFlexible.filter(match).length > 0 && (
                <p className="px-3 pt-2 pb-0.5 text-[10px] uppercase tracking-wide text-text-muted">
                  Orden
                </p>
              )}
              {visibleFlexible.filter(match).map((opt, index, list) => (
                <div key={opt.value} className="column-settings-row">
                  <button
                    type="button"
                    className="column-settings-check"
                    role="option"
                    aria-selected="true"
                    onClick={() => onToggle(opt.value)}
                  >
                    <Check size={14} className="text-primary flex-shrink-0" aria-hidden="true" />
                    <span className="min-w-0 truncate">{opt.label}</span>
                  </button>
                  <span className="flex flex-shrink-0">
                    <button
                      type="button"
                      className="column-settings-move"
                      aria-label={`Subir ${opt.label}`}
                      disabled={index === 0}
                      onClick={() => onMove(opt.value, -1)}
                    >
                      <ChevronUp size={14} />
                    </button>
                    <button
                      type="button"
                      className="column-settings-move"
                      aria-label={`Bajar ${opt.label}`}
                      disabled={index === list.length - 1}
                      onClick={() => onMove(opt.value, 1)}
                    >
                      <ChevronDown size={14} />
                    </button>
                  </span>
                </div>
              ))}

              {hiddenRows.filter(match).length > 0 && (
                <p className="px-3 pt-2 pb-0.5 text-[10px] uppercase tracking-wide text-text-muted">
                  Ocultas
                </p>
              )}
              {hiddenRows.filter(match).map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  role="option"
                  aria-selected="false"
                  className="column-settings-row column-settings-check w-full"
                  onClick={() => onToggle(opt.value)}
                >
                  <span className="column-settings-empty" aria-hidden="true" />
                  <span className="min-w-0 truncate">{opt.label}</span>
                </button>
              ))}
            </div>
          </>,
          document.body
        )}
    </div>
  )
}
