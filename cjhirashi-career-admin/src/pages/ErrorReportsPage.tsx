import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Check, RotateCcw, Trash2, X } from 'lucide-react'
import {
  useErrorReport,
  useErrorReportDelete,
  useErrorReports,
  useErrorReportSummary,
  useErrorReportUpdate,
} from '@/hooks/useErrorReports'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'
import { getErrorMessage } from '@/utils/errors'
import { formatCellValue } from '@/components/career/careerFieldUtils'
import { ColumnConfig, SelectOption } from '@/config/careerResources'
import {
  DetailSectionTemplate,
  SectionRecordView,
  TableSectionTemplate,
  useSectionTable,
} from '@/components/section'
import { ErrorReportItem, SEVERITY_LABEL } from '@/types/errorReports'

const SECTION_TITLE = 'Reportes de Falla'
const LIST_PATH = '/settings/error-reports'
const PAGE_SIZE = 50

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
  const [severityFilter, setSeverityFilter] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState<string[]>(['pending'])
  const [page, setPage] = useState(1)

  const resolvedParam = statusFilter.length === 1 ? statusFilter[0] === 'resolved' : undefined
  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(searchInput.trim()), 300)
    return () => window.clearTimeout(t)
  }, [searchInput])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, severityFilter, statusFilter])

  const params = useMemo(
    () => ({
      resolved: resolvedParam,
      severity: severityFilter.length === 1 ? severityFilter[0] : undefined,
      q: debouncedSearch || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
    [resolvedParam, severityFilter, debouncedSearch, page],
  )

  const { data, isLoading, isError, error } = useErrorReports(params)
  const { data: summary } = useErrorReportSummary()

  const severityFilteredRows = useMemo(() => {
    const items = data?.items ?? []
    return severityFilter.length > 1
      ? items.filter((r) => severityFilter.includes(String(r.severity)))
      : items
  }, [data, severityFilter])

  const { visibleColumns, columnSettings, sort, toggleSort, rows } = useSectionTable<ErrorReportItem>({
    storageKey: 'error-reports',
    columns: REPORT_COLUMNS,
    pinnedKeys: ['id'],
    rows: severityFilteredRows,
  })

  const filtersActive = severityFilter.length > 0 || statusFilter.length > 0

  const renderCell = (row: ErrorReportItem, key: string): React.ReactNode | undefined => {
    if (key === 'severity') return <SeverityBadge severity={String(row.severity)} />
    if (key === 'resolved') return <StatusBadge resolved={row.resolved} />
    if (key === 'source') {
      return (
        <span className="mono text-xs" title={row.source}>
          {row.source}
        </span>
      )
    }
    return undefined
  }

  const headerExtra = (key: string): React.ReactNode => {
    if (key === 'severity') {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Severidad"
          value={severityFilter}
          onChange={setSeverityFilter}
          options={SEVERITY_OPTIONS}
        />
      )
    }
    if (key === 'resolved') {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Estado"
          value={statusFilter}
          onChange={setStatusFilter}
          options={STATUS_OPTIONS}
        />
      )
    }
    return null
  }

  return (
    <TableSectionTemplate<ErrorReportItem>
      title={SECTION_TITLE}
      count={summary ? summary.pending : undefined}
      query={{ isLoading, isError, error }}
      toolbar={{
        search: {
          value: searchInput,
          onChange: setSearchInput,
          placeholder: 'Buscar en el mensaje del error...',
        },
        filtersActive,
        onClearFilters: () => {
          setSeverityFilter([])
          setStatusFilter([])
        },
        columnSettings,
      }}
      table={{
        columns: visibleColumns,
        rows,
        getRowKey: (r) => r.id,
        sort,
        onToggleSort: toggleSort,
        onRowClick: (r) => navigate(`${LIST_PATH}/${r.id}`),
        renderCell,
        headerExtra,
        emptyMessage:
          debouncedSearch || filtersActive
            ? 'Sin reportes para esa búsqueda o filtros.'
            : 'No hay reportes de falla registrados.',
      }}
      footer={{
        variant: 'pager',
        page,
        hasMore: Boolean(data?.has_more),
        onPageChange: setPage,
        pageSize: PAGE_SIZE,
        total: data?.total,
      }}
    />
  )
}

// ===========================================================================
// Detalle
// ===========================================================================

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

  if (isLoading) return <LoadingSpinner fullScreen={false} message="Cargando reporte..." />
  if (isError) {
    return <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
  }
  if (!data) return <p className="text-text-secondary">Reporte no encontrado.</p>

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

  const actions = data.resolved ? (
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
    <DetailSectionTemplate
      sectionTitle={SECTION_TITLE}
      listPath={LIST_PATH}
      record={{ id: data.id, name: data.source }}
      actions={actions}
    >
      {update.isError && (
        <p className="text-red-600 dark:text-red-400 text-sm mb-4">{getErrorMessage(update.error)}</p>
      )}

      <div className="space-y-6">
        <SectionRecordView
          groups={[
            {
              title: 'Información',
              fields: [
                { label: 'Severidad', value: <SeverityBadge severity={String(data.severity)} /> },
                { label: 'Estado', value: <StatusBadge resolved={data.resolved} /> },
                {
                  label: 'Origen',
                  wide: true,
                  value: <span className="mono text-xs break-all">{data.source}</span>,
                },
                { label: 'Tipo', value: data.error_type || '—' },
                { label: 'Ocurrencias', value: data.occurrences },
                { label: 'Primera vez', value: formatCellValue(data.first_seen_at, 'datetime') },
                { label: 'Última vez', value: formatCellValue(data.last_seen_at, 'datetime') },
                {
                  label: 'Mensaje',
                  wide: true,
                  value: <p className="whitespace-pre-wrap break-words">{data.message}</p>,
                },
              ],
            },
          ]}
        />

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
          <SectionRecordView
            groups={[
              {
                title: 'Resolución',
                fields: [
                  { label: 'Resuelto por', value: data.resolved_by || '—' },
                  { label: 'Fecha', value: formatCellValue(data.resolved_at, 'datetime') },
                  {
                    label: 'Notas',
                    wide: true,
                    value: <p className="whitespace-pre-wrap">{data.resolution_notes || '—'}</p>,
                  },
                ],
              },
            ]}
          />
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
              Confirma con el botón ✓ del encabezado. Marcar resuelto significa que el problema
              ya no puede volver a ocurrir por la misma causa.
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
    </DetailSectionTemplate>
  )
}

export default ErrorReportsPage
