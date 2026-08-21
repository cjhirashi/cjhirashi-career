import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ClipboardList, Trash2 } from 'lucide-react'
import { useAgentTasks, useAgentTaskMutations } from '@/hooks/useBedrockChat'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'
import { BedrockTask } from '@/types/bedrock'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  in_progress: 'En progreso',
  done: 'Hecha',
  cancelled: 'Cancelada',
}

const STATUS_COLUMNS: BedrockTask['status'][] = ['pending', 'in_progress', 'done', 'cancelled']

export const AgentTasksPage: React.FC = () => {
  const { data: tasks, isLoading, isError, error } = useAgentTasks()
  const { updateMutation, deleteMutation } = useAgentTaskMutations()

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Tareas del Agente</h1>
        <p className="text-text-secondary mt-2">
          Los planes de trabajo que Agent Bedrock arma para peticiones de varios pasos - puede retomarlos en otra
          conversación si esta se corta a la mitad.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando tareas..." />}
      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

      {tasks && tasks.length === 0 && (
        <div className="card p-8 text-center">
          <ClipboardList className="mx-auto text-text-muted mb-2" size={28} aria-hidden="true" />
          <p className="text-text-secondary text-sm">
            El agente todavía no ha planeado ninguna tarea - las crea solo cuando una petición requiere varios pasos.
          </p>
        </div>
      )}

      {tasks && tasks.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {STATUS_COLUMNS.map((status) => {
            const columnTasks = tasks.filter((t) => t.status === status)
            return (
              <div key={status} className="space-y-2">
                <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wide px-1">
                  {STATUS_LABELS[status] ?? status} · {columnTasks.length}
                </h2>
                {columnTasks.map((task) => (
                  <div key={task.id} className="card">
                    <div className="card-body space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium text-text">{task.title}</p>
                        <button
                          type="button"
                          onClick={() => {
                            if (window.confirm(`¿Eliminar la tarea "${task.title}"?`)) deleteMutation.mutate(task.id)
                          }}
                          aria-label="Eliminar tarea"
                          title="Eliminar"
                          className="p-1 rounded-lg text-text-muted hover:bg-glass hover:text-red-500 transition-colors flex-shrink-0"
                        >
                          <Trash2 size={13} aria-hidden="true" />
                        </button>
                      </div>
                      {task.description && (
                        <div className="markdown-body markdown-body-compact text-xs">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{task.description}</ReactMarkdown>
                        </div>
                      )}
                      <select
                        value={task.status}
                        onChange={(e) => updateMutation.mutate({ id: task.id, payload: { status: e.target.value } })}
                        className="input-field text-xs py-1"
                        aria-label={`Estado de "${task.title}"`}
                      >
                        {STATUS_COLUMNS.map((s) => (
                          <option key={s} value={s}>
                            {STATUS_LABELS[s]}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
