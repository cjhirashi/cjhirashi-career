import React, { useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowLeft,
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
  useErrorReportUpdate,
} from '@/hooks/useErrorReports'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ThemedSelect } from '@/components/ThemedSelect'
import { getErrorMessage } from '@/utils/errors'
import { ErrorReportItem, SEVERITY_LABEL } from '@/types/errorReports'

const STATUS_OPTIONS = [
  { value: 'pending', label: 'Pendientes' },
  { value: 'resolved', label: 'Resueltos' },
  { value: 'all', label: 'Todos' },
]

const SEVERITY_OPTIONS = [
  { value: '', label: 'Todas las severidades' },
  { value: 'critical', label: 'Crítico' },
  { value: 'error', label: 'Error' },
  { value: 'warning', label: 'Aviso' },
]

const SEVERITY_CLASS: Record<string, string> = {
  critical: 'bg-red-500/15 text-red-600 dark:text-red-400',
  error: 'bg-orange-500/15 text-orange-600 dark:text-orange-400',
  warning: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400',
}

function fmt(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' })
}

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => (
  <span
    className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${
      SEVERITY_CLASS[severity] ?? 'bg-muted text-muted-foreground'
    }`}
  >
    {SEVERITY_LABEL[severity] ?? severity}
  </span>
)

// ---------------------------------------------------------------------------
// Detalle
// ---------------------------------------------------------------------------

const ErrorReportDetailPanel: React.FC<{ reportId: string; onBack: () => void }> = ({
  reportId,
  onBack,
}) => {
  const { data, isLoading, isError, error } = useErrorReport(reportId)
  const update = useErrorReportUpdate()
  const remove = useErrorReportDelete()
  const navigate = useNavigate()
  const [notes, setNotes] = useState('')

  if (isLoading) return <LoadingSpinner />
  if (isError || !data) {
    return (
      <div className="text-sm text-red-500">
        {getErrorMessage(error) || 'No se pudo cargar el reporte.'}
      </div>
    )
  }

  const resolve = async () => {
    await update.mutateAsync({
      reportId,
      resolved: true,
      resolutionNotes: notes.trim() || data.resolution_notes || null,
    })
  }
  const reopen = async () => {
    await update.mutateAsync({ reportId, resolved: false })
  }
  const del = async () => {
    if (!window.confirm('¿Eliminar este reporte de forma permanente?')) return
    await remove.mutateAsync(reportId)
    navigate('/settings/error-reports')
  }

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} /> Volver a la lista
      </button>

      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge severity={String(data.severity)} />
        <span className="font-mono text-xs text-muted-foreground">{data.id}</span>
        <span
          className={`rounded px-1.5 py-0.5 text-xs font-medium ${
            data.resolved
              ? 'bg-green-500/15 text-green-600 dark:text-green-400'
              : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
          }`}
        >
          {data.resolved ? 'Resuelto' : 'Pendiente'}
        </span>
        {data.occurrences > 1 && (
          <span className="text-xs text-muted-foreground">×{data.occurrences} ocurrencias</span>
        )}
      </div>

      <div>
        <div className="text-xs uppercase tracking-wide text-muted-foreground">Origen</div>
        <div className="font-mono text-sm break-all">{data.source}</div>
      </div>

      <div>
        <div className="text-xs uppercase tracking-wide text-muted-foreground">Mensaje</div>
        <div className="text-sm whitespace-pre-wrap break-words">{data.message}</div>
        {data.error_type && (
          <div className="mt-1 text-xs text-muted-foreground">Tipo: {data.error_type}</div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Primera vez</div>
          {fmt(data.first_seen_at)}
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Última vez</div>
          {fmt(data.last_seen_at)}
        </div>
      </div>

      {data.stack_trace && (
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Traceback</div>
          <pre className="mt-1 max-h-80 overflow-auto rounded bg-muted p-3 text-xs leading-relaxed">
            {data.stack_trace}
          </pre>
        </div>
      )}

      {data.context && Object.keys(data.context).length > 0 && (
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Contexto</div>
          <pre className="mt-1 max-h-60 overflow-auto rounded bg-muted p-3 text-xs">
            {JSON.stringify(data.context, null, 2)}
          </pre>
        </div>
      )}

      <div className="rounded border border-border p-3">
        {data.resolved ? (
          <div className="space-y-2">
            <div className="text-sm">
              Resuelto por <strong>{data.resolved_by ?? '—'}</strong> el {fmt(data.resolved_at)}
            </div>
            {data.resolution_notes && (
              <div className="text-sm whitespace-pre-wrap text-muted-foreground">
                {data.resolution_notes}
              </div>
            )}
            <button
              type="button"
              onClick={reopen}
              disabled={update.isPending}
              className="inline-flex items-center gap-1 rounded border border-border px-3 py-1.5 text-sm hover:bg-muted"
            >
              <RotateCcw size={14} /> Reabrir
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Notas de resolución (qué se hizo para corregirlo)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full rounded border border-border bg-background p-2 text-sm"
              placeholder="Ej.: corregido validando el payload antes de guardar; commit abc123"
            />
            <button
              type="button"
              onClick={resolve}
              disabled={update.isPending}
              className="inline-flex items-center gap-1 rounded bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              <Check size={14} /> Marcar como resuelto
            </button>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={del}
        disabled={remove.isPending}
        className="inline-flex items-center gap-1 text-xs text-red-500 hover:text-red-600"
      >
        <Trash2 size={13} /> Eliminar reporte
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Lista
// ---------------------------------------------------------------------------

export const ErrorReportsPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>()
  const navigate = useNavigate()

  const [status, setStatus] = useState('pending')
  const [severity, setSeverity] = useState('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)

  const params = useMemo(
    () => ({
      resolved: status === 'all' ? undefined : status === 'resolved',
      severity: severity || undefined,
      q: q.trim() || undefined,
      page,
      page_size: 50,
    }),
    [status, severity, q, page],
  )

  const { data, isLoading, isError, error } = useErrorReports(params)

  if (reportId) {
    return (
      <div className="p-4 max-w-3xl">
        <ErrorReportDetailPanel
          reportId={reportId}
          onBack={() => navigate('/settings/error-reports')}
        />
      </div>
    )
  }

  return (
    <div className="p-4 space-y-4">
      <header className="flex items-center gap-2">
        <AlertTriangle size={20} className="text-amber-500" />
        <h1 className="text-lg font-semibold">Reportes de Falla</h1>
      </header>
      <p className="text-sm text-muted-foreground max-w-2xl">
        Errores capturados automáticamente en cualquier parte del sistema. Un reporte pendiente
        aún no se ha revisado; márcalo como resuelto cuando el problema ya se corrigió en el
        código.
      </p>

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-40">
          <label className="block text-xs text-muted-foreground mb-1">Estado</label>
          <ThemedSelect
            value={status}
            onChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
            options={STATUS_OPTIONS}
          />
        </div>
        <div className="w-52">
          <label className="block text-xs text-muted-foreground mb-1">Severidad</label>
          <ThemedSelect
            value={severity}
            onChange={(v) => {
              setSeverity(v)
              setPage(1)
            }}
            options={SEVERITY_OPTIONS}
          />
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs text-muted-foreground mb-1">Buscar en el mensaje</label>
          <div className="relative">
            <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              value={q}
              onChange={(e) => {
                setQ(e.target.value)
                setPage(1)
              }}
              className="w-full rounded border border-border bg-background py-1.5 pl-7 pr-7 text-sm"
              placeholder="texto del error…"
            />
            {q && (
              <button
                type="button"
                onClick={() => setQ('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X size={14} />
              </button>
            )}
          </div>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : isError ? (
        <div className="text-sm text-red-500">
          {getErrorMessage(error) || 'No se pudieron cargar los reportes.'}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="rounded border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
          No hay reportes que coincidan con el filtro.
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">Sev.</th>
                  <th className="px-3 py-2">Origen</th>
                  <th className="px-3 py-2">Mensaje</th>
                  <th className="px-3 py-2 text-right">Rep.</th>
                  <th className="px-3 py-2">Última vez</th>
                  <th className="px-3 py-2">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((row: ErrorReportItem) => (
                  <tr
                    key={row.id}
                    onClick={() => navigate(`/settings/error-reports/${row.id}`)}
                    className="cursor-pointer border-t border-border hover:bg-muted/40"
                  >
                    <td className="px-3 py-2">
                      <SeverityBadge severity={String(row.severity)} />
                    </td>
                    <td className="px-3 py-2 font-mono text-xs max-w-[220px] truncate" title={row.source}>
                      {row.source}
                    </td>
                    <td className="px-3 py-2 max-w-[420px] truncate" title={row.message}>
                      {row.message}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">{row.occurrences}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-muted-foreground">
                      {fmt(row.last_seen_at)}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                          row.resolved
                            ? 'bg-green-500/15 text-green-600 dark:text-green-400'
                            : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                        }`}
                      >
                        {row.resolved ? 'Resuelto' : 'Pendiente'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{data.total} reporte(s)</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded border border-border px-2 py-1 disabled:opacity-40"
              >
                Anterior
              </button>
              <span>Página {page}</span>
              <button
                type="button"
                disabled={!data.has_more}
                onClick={() => setPage((p) => p + 1)}
                className="rounded border border-border px-2 py-1 disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ErrorReportsPage
