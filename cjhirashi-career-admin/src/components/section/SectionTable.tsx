import React from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ColumnConfig } from '@/config/careerResources'
import { formatCellValue } from '@/components/career/careerFieldUtils'
import { SortState } from '@/utils/tableColumns'

interface SectionTableState {
  isLoading?: boolean
  isError?: boolean
  errorMessage?: string
  onRetry?: () => void
}

interface SectionTableProps<Row> {
  columns: ColumnConfig[]
  rows: Row[]
  getRowKey: (row: Row) => string
  /** Column key used for the pinned/highlighted id cell (default `id`). */
  idColumnKey?: string
  sort?: SortState
  onToggleSort?: (key: string) => void
  onRowClick?: (row: Row) => void
  /** Extra class(es) per row (e.g. status tint). */
  rowClassName?: (row: Row) => string
  /** Per-column cell override. Return `undefined` to fall back to `formatCellValue`. */
  renderCell?: (row: Row, colKey: string) => React.ReactNode | undefined
  /** Extra node in a column header, right of the sort toggle (e.g. a filter button). */
  headerExtra?: (colKey: string) => React.ReactNode
  /** Trailing right-aligned actions column. */
  rowActions?: (row: Row) => React.ReactNode
  actionsLabel?: string
  state?: SectionTableState
  emptyMessage: string
}

/**
 * The list `<table>` shared by every section: sticky sortable header, id
 * highlight, per-column filter slot, optional trailing actions column, and the
 * loading / error / empty states — all inside `.table-scroll`.
 */
export function SectionTable<Row>({
  columns,
  rows,
  getRowKey,
  idColumnKey = 'id',
  sort,
  onToggleSort,
  onRowClick,
  rowClassName,
  renderCell,
  headerExtra,
  rowActions,
  actionsLabel = 'Acciones',
  state,
  emptyMessage,
}: SectionTableProps<Row>) {
  if (state?.isLoading) {
    return (
      <div className="table-scroll table-scroll-inset">
        <LoadingSpinner fullScreen={false} message="Cargando..." />
      </div>
    )
  }

  if (state?.isError) {
    return (
      <div className="table-scroll table-scroll-inset text-center py-6">
        <p className="text-red-600 dark:text-red-400 text-sm">
          {state.errorMessage ?? 'No se pudo cargar la información.'}
        </p>
        {state.onRetry && (
          <button type="button" onClick={state.onRetry} className="btn-secondary btn-small mt-3">
            Reintentar
          </button>
        )}
      </div>
    )
  }

  if (rows.length === 0) {
    return (
      <p className="table-scroll table-scroll-inset text-text-secondary text-sm text-center py-6">
        {emptyMessage}
      </p>
    )
  }

  const renderRowCells = (row: Row) =>
    columns.map((col) => {
      const override = renderCell?.(row, col.key)
      if (override !== undefined) {
        return (
          <td
            key={col.key}
            className={`px-6 py-2${col.key === idColumnKey ? ' table-col-id' : ''}`}
          >
            {override}
          </td>
        )
      }
      const value = (row as Record<string, unknown>)[col.key]
      if (col.key === idColumnKey) {
        return (
          <td key={col.key} className="px-6 py-2 table-col-id" title={String(value ?? '')}>
            {value != null && value !== '' ? String(value) : '—'}
          </td>
        )
      }
      return (
        <td
          key={col.key}
          className={`px-6 py-2 text-text${col.format === 'truncate' ? '' : ' whitespace-nowrap'}`}
        >
          {formatCellValue(value, col.format)}
        </td>
      )
    })

  return (
    <div className="table-scroll">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-text-secondary">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-6 py-2 font-medium whitespace-nowrap${
                  col.key === idColumnKey ? ' table-col-id' : ''
                }`}
              >
                <span className="inline-flex items-center gap-0.5">
                  {onToggleSort ? (
                    <button
                      type="button"
                      onClick={() => onToggleSort(col.key)}
                      className={`flex items-center gap-1 ${
                        col.key === idColumnKey ? 'hover:opacity-80' : 'hover:text-text'
                      }`}
                    >
                      {col.label}
                      {sort?.key === col.key ? (
                        sort.dir === 'asc' ? (
                          <ArrowUp size={12} />
                        ) : (
                          <ArrowDown size={12} />
                        )
                      ) : (
                        <ArrowUpDown size={12} className="opacity-30" />
                      )}
                    </button>
                  ) : (
                    <span>{col.label}</span>
                  )}
                  {headerExtra?.(col.key)}
                </span>
              </th>
            ))}
            {rowActions && <th className="px-6 py-2 font-medium text-right">{actionsLabel}</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const cls = `border-b border-border last:border-0${
              onRowClick ? ' hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer' : ''
            }${rowClassName ? ` ${rowClassName(row)}` : ''}`
            return (
              <tr
                key={getRowKey(row)}
                className={cls}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {renderRowCells(row)}
                {rowActions && (
                  <td className="px-6 py-2 text-right whitespace-nowrap">{rowActions(row)}</td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
