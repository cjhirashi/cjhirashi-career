import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Check,
  RotateCcw,
  Search,
  Trash2,
  X,
} from 'lucide-react'
import {
  useErrorReport,
  useErrorReportDelete,
  useErrorReports,
  useErrorReportSummary,
  useErrorReportUpdate,
} from '@/hooks/useErrorReports'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { SectionViewTabs } from '@/components/SectionViewTabs'
import { TableColumnSettings } from '@/components/career/TableColumnSettings'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'
import { useVisibleTableColumns } from '@/hooks/useVisibleTableColumns'
import { formatCellValue } from '@/components/career/careerFieldUtils'
import { getErrorMessage } from '@/utils/errors'
import { ColumnConfig, SelectOption } from '@/config/careerResources'
import { ErrorReportItem, SEVERITY_LABEL } from '@/types/errorReports'

const REPORT_TABS = [
  { key: 'list', label: 'Lista' },
  { key: 'view', label: 'Detalle' },
]

const REPORT_COLUMNS: ColumnConfig[] = [
  { key: 'id', label: 'ID' },
  { key: 'severity', label: 'Severidad' },
  { key: 'source', label: 'Origen' },
  { key: 'error_type', label: 'Tipo' },
  { key: 'message', label: 'Mensaje', format: 'truncate' },
  { key: 'occurrences', label: 'Reps', format: 'number' },
  { key: 'last_seen_at', label: 'Última vez', format: 'datetime' },
  { key: 'resolved', label: 'Estado' },
]

const REPORT_PINNED = ['id']
const REPORT_DEFAULT_KEYS = REPORT_COLUMNS.map((col) => col.key)

const SEVERITY_OPTIONS: SelectOption[] = [
  { value: 'critical', label: 'Crítico' },
  { value: 'error', label: 'Error' },
  { value: 'warning', label: 'Aviso' },
]

const STATUS_OPTIONS: SelectOption[] = [
  { value: 'pending', label: 'Pendiente' },
  { value: 'resolved', label: 'Resuelto' },
]

const SEVERITY_BADGE: Record<string, string> = {
  critical: 'badge badge-error',
  error: 'badge badge-error',
  warning: 'badge badge-warning',
}

const compareCells = (a: unknown, b: unknown, dir: 'asc' | 'desc'): number => {
  const av = a == null ? '' : String(a).toLowerCase()
  const bv = b == null ? '' : String(b).toLowerCase()
  const cmp = av.localeCompare(bv, 'es', { numeric: true })
  return dir === 'asc' ? cmp : -cmp
}

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => (
  <span className={SEVERITY_BADGE[severity] ?? 'badge badge-slate'}>
    {SEVERITY_LABEL[severity] ?? severity}
  </span>
)

const StatusBadge: React.FC<{ resolved: boolean }> = ({ resolved }) => (
  <span className={resolved ? 'badge badge-success' : 'badge badge-warning'}>
    {resolved ? 'Resuelto' : 'Pendiente'}
  </span>
)

// ===========================================================================
// Lista
// ===========================================================================

export const ErrorReportsPage: React.FC = () => {
  const navigate = useNavigate()
  const { columns, selectedKeys, toggleColumn, moveColumn, options, pinnedKeys } =
    useVisibleTableColumns('error-reports', REPORT_COLUMNS, REPORT_DEFAULT_KEYS, REPORT_PINNED)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState<string[]>(['pending'])
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<string | undefined>(undefined)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(searchInput.trim()), 300)
    return () => window.clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    setPage(1)
  }, [search, severityFilter, statusFilter])

  const resolvedParam =
    statusFilter.length === 1 ? statusFilter[0] === 'resolved' : undefined

  const params = useMemo(
    () => ({
      resolved: resolvedParam,
      severity: severityFilter.length === 1 ? severityFilter[0] : undefined,
      q: search || undefined,
      page,
      page_size: 50,
    }),
    [resolvedParam, severityFilter, search, page],
  )

  const { data, isLoading, isError, error } = useErrorReports(params)
  const { data: summary } = useErrorReportSummary()

  const rows = useMemo(() => {
    let next = data?.items ?? []
    // Filtro multi-severidad en cliente cuando hay más de una seleccionada
    // (el endpoint sólo acepta una).
    if (severityFilter.length > 1) {
      next = next.filter((row) => severityFilter.includes(String(row.severity)))
    }
    if (sortBy) {
      next = [...next].sort((a, b) =>
        compareCells(a[sortBy as keyof ErrorReportItem], b[sortBy as keyof ErrorReportItem], sortDir),
      )
    }
    return next
  }, [data, severityFilter, sortBy, sortDir])

  const toggleSort = (key: string) => {
    setSortBy((current) => {
      if (current !== key) {
        setSortDir('asc')
        return key
      }
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'))
      return key
    })
  }

  const total = data?.total ?? 0
  const filtersActive = severityFilter.length > 0 || statusFilter.length > 0

  const renderCell = (row: ErrorReportItem, key: string) => {
    if (key === 'id') {
      return (
        <td key="id" className="px-6 py-2 table-col-id" title={row.id}>
          {row.id}
        </td>
      )
    }
    if (key === 'severity') {
      return (
        <td key="severity" className="px-6 py-2">
          <SeverityBadge severity={String(row.severity)} />
        </td>
      )
    }
    if (key === 'resolved') {
      return (
        <td key="resolved" className="px-6 py-2">
          <StatusBadge resolved={row.resolved} />
        </td>
      )
    }
    if (key === 'source') {
      return (
        <td key="source" className="px-6 py-2 mono text-xs" title={row.source}>
          {row.source}
        </td>
      )
    }
    return (
      <td
        key={key}
        className={`px-6 py-2 text-text${
          REPORT_COLUMNS.find((c) => c.key === key)?.format === 'truncate' ? '' : ' whitespace-nowrap'
        }`}
      >
        {formatCellValue(
          row[key as keyof ErrorReportItem],
          REPORT_COLUMNS.find((c) => c.key === key)?.format,
        )}
      </td>
    )
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="card has-view-tabs">
        <div className="card-header">
          <h2 className="font-semibold text-text flex items-center gap-2 min-w-0">
            <span className="truncate">Reportes de Falla</span>
            {summary && (
              <span className="badge badge-slate mono" title="Pendientes / resueltos">
                {summary.pending} · {summary.resolved}
              </span>
            )}
          </h2>
          <div className="view-tabs-row">
            <SectionViewTabs views={REPORT_TABS} activeKey="list" interactiveKeys={[]} />
          </div>
        </div>
        <div className="card-body table-list-body">
          {isLoading && (
            <div className="table-scroll table-scroll-inset">
              <LoadingSpinner fullScreen={false} message="Cargando reportes..." />
            </div>
          )}
          {isError && (
            <p className="table-scroll table-scroll-inset text-red-600 dark:text-red-400 text-sm">
              {getErrorMessage(error)}
            </p>
          )}

          {!isLoading && !isError && (
            <>
              <div className="table-toolbar flex flex-wrap items-center gap-2 mb-4">
                <div className="relative flex-1 min-w-[200px]">
                  <Search
                    size={14}
                    className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-secondary"
                  />
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Buscar en el mensaje del error..."
                    className="input-field pl-8 pr-8 py-1.5 text-sm w-full"
                  />
                  {searchInput && (
                    <button
                      type="button"
                      onClick={() => setSearchInput('')}
                      aria-label="Limpiar búsqueda"
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
                {filtersActive && (
                  <button
                    type="button"
                    className="btn-secondary btn-small"
                    onClick={() => {
                      setSeverityFilter([])
                      setStatusFilter([])
                    }}
                  >
                    Limpiar filtros
                  </button>
                )}
                <div className="ml-auto flex-shrink-0">
                  <TableColumnSettings
                    options={options}
                    value={selectedKeys}
                    pinnedKeys={pinnedKeys}
                    onToggle={toggleColumn}
                    onMove={moveColumn}
                  />
                </div>
              </div>

              {rows.length === 0 ? (
                <p className="table-scroll table-scroll-inset text-text-secondary text-sm text-center py-6">
                  {search || filtersActive
                    ? 'Sin reportes para esa búsqueda o filtros.'
                    : 'No hay reportes de falla registrados.'}
                </p>
              ) : (
                <div className="table-scroll">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-text-secondary">
                        {columns.map((col) => (
                          <th
                            key={col.key}
                            className={`px-6 py-2 font-medium whitespace-nowrap${
                              col.key === 'id' ? ' table-col-id' : ''
                            }`}
                          >
                            <span className="inline-flex items-center gap-0.5">
                              <button
                                type="button"
                                onClick={() => toggleSort(col.key)}
                                className={`flex items-center gap-1 ${
                                  col.key === 'id' ? 'hover:opacity-80' : 'hover:text-text'
                                }`}
                              >
                                {col.label}
                                {sortBy === col.key ? (
                                  sortDir === 'asc' ? (
                                    <ArrowUp size={12} />
                                  ) : (
                                    <ArrowDown size={12} />
                                  )
                                ) : (
                                  <ArrowUpDown size={12} className="opacity-30" />
                                )}
                              </button>
                              {col.key === 'severity' && (
                                <ThemedMultiSelect
                                  variant="icon"
                                  aria-label="Severidad"
                                  value={severityFilter}
                                  onChange={setSeverityFilter}
                                  options={SEVERITY_OPTIONS}
                                />
                              )}
                              {col.key === 'resolved' && (
                                <ThemedMultiSelect
                                  variant="icon"
                                  aria-label="Estado"
                                  value={statusFilter}
                                  onChange={setStatusFilter}
                                  options={STATUS_OPTIONS}
                                />
                              )}
                            </span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row) => (
                        <tr
                          key={row.id}
                          className="border-b border-border last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer"
                          onClick={() => navigate(`/settings/error-reports/${row.id}`)}
                        >
                          {columns.map((col) => renderCell(row, col.key))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="table-footer flex items-center justify-between">
                <span className="text-xs text-text-secondary">
                  {total === 0 ? 0 : (page - 1) * 50 + 1}–{(page - 1) * 50 + rows.length} de {total}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="btn-secondary btn-small"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Anterior
                  </button>
                  <span className="text-xs text-text-secondary">Página {page}</span>
                  <button
                    type="button"
                    className="btn-secondary btn-small"
                    disabled={!data?.has_more}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ===========================================================================
// Detalle
// ===========================================================================

const Field: React.FC<{ label: string; children: React.ReactNode; wide?: boolean }> = ({
  label,
  children,
  wide,
}) => (
  <div className={wide ? 'md:col-span-2' : ''}>
    <dt className="text-xs text-text-secondary mb-1">{label}</dt>
    <dd className="text-sm text-text">{children}</dd>
  </div>
)

export const ErrorReportDetailPage: React.FC = () => {
  const navigate = useNavigate()
  const { reportId = '' } = useParams<{ reportId: string }>()
  const { data, isLoading, isError, error } = useErrorReport(reportId)
  const update = useErrorReportUpdate()
  const remove = useErrorReportDelete()
  const [resolving, setResolving] = useState(false)
  const [notes, setNotes] = useState('')

  useEffect(() => {
    setResolving(false)
    setNotes('')
  }, [reportId])

  if (isLoading) {
    return <LoadingSpinner fullScreen={false} message="Cargando reporte..." />
  }
  if (isError) {
    return <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
  }
  if (!data) {
    return <p className="text-text-secondary">Reporte no encontrado.</p>
  }

  const doResolve = () =>
    update.mutate(
      { reportId, resolved: true, resolutionNotes: notes.trim() || data.resolution_notes || null },
      { onSuccess: () => setResolving(false) },
    )
  const doReopen = () => update.mutate({ reportId, resolved: false })
  const doDelete = () => {
    if (!window.confirm('¿Eliminar este reporte de forma permanente?')) return
    remove.mutate(reportId, { onSuccess: () => navigate('/settings/error-reports') })
  }

  const headerActions = data.resolved ? (
    <button
      type="button"
      onClick={doReopen}
      className="btn-icon btn-icon-sm"
      aria-label="Reabrir"
      title="Reabrir"
      disabled={update.isPending}
    >
      <RotateCcw size={13} />
    </button>
  ) : resolving ? (
    <>
      <button
        type="button"
        onClick={() => setResolving(false)}
        className="btn-icon btn-icon-sm btn-icon-muted"
        aria-label="Cancelar"
        title="Cancelar"
        disabled={update.isPending}
      >
        <X size={13} />
      </button>
      <button
        type="button"
        onClick={doResolve}
        className="btn-icon btn-icon-sm"
        aria-label="Confirmar resolución"
        title="Confirmar resolución"
        disabled={update.isPending}
      >
        <Check size={13} />
      </button>
    </>
  ) : (
    <button
      type="button"
      onClick={() => setResolving(true)}
      className="btn-icon btn-icon-sm"
      aria-label="Marcar como resuelto"
      title="Marcar como resuelto"
    >
      <Check size={13} />
    </button>
  )

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="card has-view-tabs">
        <div className="card-header">
          <h2 className="font-semibold text-text flex items-center gap-2 min-w-0">
            <span className="truncate">Reportes de Falla</span>
            <span className="text-text-muted font-normal">·</span>
            <span className="mono text-primary font-normal flex-shrink-0">{data.id}</span>
            <span className="text-text-muted font-normal">·</span>
            <span className="truncate mono text-xs">{data.source}</span>
          </h2>
          <div className="view-tabs-row">
            <SectionViewTabs
              views={REPORT_TABS}
              activeKey="view"
              interactiveKeys={['list']}
              onSelect={(key) => {
                if (key === 'list') navigate('/settings/error-reports')
              }}
            />
            <div className="view-tabs-actions">{headerActions}</div>
          </div>
        </div>
        <div className="card-body">
          {update.isError && (
            <p className="text-red-600 dark:text-red-400 text-sm mb-4">
              {getErrorMessage(update.error)}
            </p>
          )}

          <div className="space-y-6">
            <div>
              <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                Información
              </h3>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Field label="Severidad">
                  <SeverityBadge severity={String(data.severity)} />
                </Field>
                <Field label="Estado">
                  <StatusBadge resolved={data.resolved} />
                </Field>
                <Field label="Origen" wide>
                  <span className="mono text-xs break-all">{data.source}</span>
                </Field>
                <Field label="Tipo">{data.error_type || '—'}</Field>
                <Field label="Ocurrencias">{data.occurrences}</Field>
                <Field label="Primera vez">{formatCellValue(data.first_seen_at, 'datetime')}</Field>
                <Field label="Última vez">{formatCellValue(data.last_seen_at, 'datetime')}</Field>
                <Field label="Mensaje" wide>
                  <p className="whitespace-pre-wrap break-words">{data.message}</p>
                </Field>
              </dl>
            </div>

            {data.stack_trace && (
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                  Traceback
                </h3>
                <pre className="max-h-96 overflow-auto rounded-lg bg-slate-100 dark:bg-slate-800/60 p-3 text-xs leading-relaxed">
                  {data.stack_trace}
                </pre>
              </div>
            )}

            {data.context && Object.keys(data.context).length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                  Contexto
                </h3>
                <pre className="max-h-72 overflow-auto rounded-lg bg-slate-100 dark:bg-slate-800/60 p-3 text-xs">
                  {JSON.stringify(data.context, null, 2)}
                </pre>
              </div>
            )}

            {data.resolved ? (
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                  Resolución
                </h3>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Field label="Resuelto por">{data.resolved_by || '—'}</Field>
                  <Field label="Fecha">{formatCellValue(data.resolved_at, 'datetime')}</Field>
                  <Field label="Notas" wide>
                    <p className="whitespace-pre-wrap">{data.resolution_notes || '—'}</p>
                  </Field>
                </dl>
              </div>
            ) : resolving ? (
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                  Marcar como resuelto
                </h3>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="input-field text-sm"
                  placeholder="Qué se hizo para corregirlo (commit, cambio, etc.)"
                  aria-label="Notas de resolución"
                />
                <p className="text-xs text-text-muted mt-2">
                  Confirma con el botón ✓ del encabezado. Marcar resuelto significa que el
                  problema ya no puede volver a ocurrir por la misma causa.
                </p>
              </div>
            ) : null}

            <button
              type="button"
              onClick={doDelete}
              disabled={remove.isPending}
              className="flex items-center gap-2 text-xs text-red-500 hover:text-red-600 disabled:opacity-50"
            >
              <Trash2 size={13} aria-hidden="true" />
              Eliminar reporte
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ErrorReportsPage
