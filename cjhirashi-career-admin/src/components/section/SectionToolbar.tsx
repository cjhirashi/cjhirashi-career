import React from 'react'
import { Search, X } from 'lucide-react'
import { TableColumnSettings } from '@/components/career/TableColumnSettings'
import { SelectOption } from '@/config/careerResources'

export interface ColumnSettingsProps {
  options: SelectOption[]
  value: string[]
  pinnedKeys: string[]
  onToggle: (key: string) => void
  onMove: (key: string, direction: -1 | 1) => void
}

interface SectionToolbarProps {
  search?: {
    value: string
    onChange: (value: string) => void
    placeholder?: string
  }
  filtersActive?: boolean
  onClearFilters?: () => void
  /** Extra controls placed before the column-settings gear. */
  children?: React.ReactNode
  columnSettings?: ColumnSettingsProps
}

/** The `table-toolbar` row: search + "clear filters" + extra controls + column gear. */
export const SectionToolbar: React.FC<SectionToolbarProps> = ({
  search,
  filtersActive,
  onClearFilters,
  children,
  columnSettings,
}) => (
  <div className="table-toolbar flex flex-wrap items-center gap-2 mb-4">
    {search && (
      <div className="relative flex-1 min-w-[200px]">
        <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-secondary" />
        <input
          type="text"
          value={search.value}
          onChange={(e) => search.onChange(e.target.value)}
          placeholder={search.placeholder ?? 'Buscar...'}
          className="input-field pl-8 pr-8 py-1.5 text-sm w-full"
        />
        {search.value && (
          <button
            type="button"
            onClick={() => search.onChange('')}
            aria-label="Limpiar búsqueda"
            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text"
          >
            <X size={14} />
          </button>
        )}
      </div>
    )}

    {filtersActive && onClearFilters && (
      <button type="button" className="btn-secondary btn-small" onClick={onClearFilters}>
        Limpiar filtros
      </button>
    )}

    {children}

    {columnSettings && (
      <div className="ml-auto flex-shrink-0">
        <TableColumnSettings {...columnSettings} />
      </div>
    )}
  </div>
)
