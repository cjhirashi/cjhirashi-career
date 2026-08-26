import React from 'react'
import { RotateCcw, ScrollText } from 'lucide-react'
import { useBedrockAuditLog, useBedrockAuditRestore } from '@/hooks/useBedrockChat'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

const ACTION_LABELS: Record<string, string> = {
  create: 'Creó',
  update: 'Actualizó',
  delete: 'Eliminó',
}

const ACTION_BADGE: Record<string, 'success' | 'cyan' | 'error'> = {
  create: 'success',
  update: 'cyan',
  delete: 'error',
}

export const AgentAuditLogPage: React.FC = () => {
  const { data: entries, isLoading, isError, error } = useBedrockAuditLog(100)
  const restore = useBedrockAuditRestore()

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Bitácora del Agente</h1>
        <p className="text-text-secondary mt-2">
          Cada registro que el agente creó, actualizó o eliminó, con el estado completo antes y después del cambio -
          un registro eliminado se puede restaurar desde aquí.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando bitácora..." />}
      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

      {entries && entries.length === 0 && (
        <div className="card p-8 text-center">
          <ScrollText className="mx-auto text-text-muted mb-2" size={28} aria-hidden="true" />
          <p className="text-text-secondary text-sm">El agente todavía no ha hecho ningún cambio.</p>
        </div>
      )}

      {entries && entries.length > 0 && (
        <div className="space-y-2">
          {entries.map((entry) => (
            <div key={entry.id} className="card">
              <div className="card-body flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`badge badge-${ACTION_BADGE[entry.action] ?? 'cyan'}`}>
                      {ACTION_LABELS[entry.action] ?? entry.action}
                    </span>
                    <span className="text-sm font-mono text-text">{entry.resource_type}</span>
                    {entry.resource_id !== null && (
                      <span className="text-xs text-text-muted">#{entry.resource_id}</span>
                    )}
                    <span className="text-xs text-text-muted ml-auto">
                      {new Date(entry.created_at).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' })}
                    </span>
                  </div>

                  {entry.action === 'delete' && entry.old_values && (
                    <details className="mt-2">
                      <summary className="text-xs text-text-secondary cursor-pointer">Ver registro eliminado</summary>
                      <pre className="text-[11px] whitespace-pre-wrap break-words text-text-secondary mt-1 p-2 rounded-lg bg-glass">
                        {JSON.stringify(entry.old_values, null, 2)}
                      </pre>
                    </details>
                  )}
                  {entry.action === 'update' && (
                    <details className="mt-2">
                      <summary className="text-xs text-text-secondary cursor-pointer">Ver cambio</summary>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-1">
                        <div>
                          <p className="text-[10px] text-text-muted uppercase mb-1">Antes</p>
                          <pre className="text-[11px] whitespace-pre-wrap break-words text-text-secondary p-2 rounded-lg bg-glass">
                            {JSON.stringify(entry.old_values, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-muted uppercase mb-1">Después</p>
                          <pre className="text-[11px] whitespace-pre-wrap break-words text-text-secondary p-2 rounded-lg bg-glass">
                            {JSON.stringify(entry.new_values, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </details>
                  )}
                </div>

                {entry.action === 'delete' && (
                  <button
                    type="button"
                    onClick={() => restore.mutate(entry.id)}
                    disabled={restore.isPending}
                    title="Restaurar este registro"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-primary hover:bg-glass transition-colors disabled:opacity-50 flex-shrink-0"
                  >
                    <RotateCcw size={13} aria-hidden="true" />
                    Restaurar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
