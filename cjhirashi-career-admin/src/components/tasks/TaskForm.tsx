import React, { useEffect, useMemo, useState } from 'react'
import { ThemedSelect } from '@/components/ThemedSelect'
import { BedrockAgentCatalogItem, BedrockTask, BedrockTaskPayload } from '@/types/bedrock'
import { getErrorMessage } from '@/utils/errors'
import { datetimeLocalToIso, isoToDatetimeLocal, TASK_PRIORITY_LABELS, TASK_STATUS_LABELS } from './taskUtils'

export const TASK_FORM_ID = 'task-record-form'

interface TaskFormProps {
  task: BedrockTask | null
  agents: BedrockAgentCatalogItem[]
  onSave: (payload: BedrockTaskPayload & { title: string }) => Promise<unknown> | unknown
  isSaving: boolean
  formId?: string
  hideActions?: boolean
  onCancel?: () => void
}

const emptyForm = {
  title: '',
  description: '',
  status: 'pending',
  assignee_type: 'user',
  agent_profile_id: '',
  scheduled_at: '',
  due_at: '',
  priority: 'medium',
}

export const TaskForm: React.FC<TaskFormProps> = ({
  task,
  agents,
  onSave,
  isSaving,
  formId = TASK_FORM_ID,
  hideActions = false,
  onCancel,
}) => {
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!task) {
      setForm(emptyForm)
      setError(null)
      return
    }
    setForm({
      title: task.title,
      description: task.description ?? '',
      status: task.status,
      assignee_type: task.assignee_type === 'agent' ? 'agent' : 'user',
      agent_profile_id: task.agent_profile_id ?? '',
      scheduled_at: isoToDatetimeLocal(task.scheduled_at),
      due_at: isoToDatetimeLocal(task.due_at),
      priority: task.priority || 'medium',
    })
    setError(null)
  }, [task])

  const agentOptions = useMemo(
    () =>
      [...agents]
        .sort((a, b) => a.level - b.level || a.label.localeCompare(b.label))
        .map((agent) => ({
          value: agent.profile_id,
          label: `L${agent.level} · ${agent.label}`,
        })),
    [agents]
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!form.title.trim()) {
      setError('El título es obligatorio.')
      return
    }
    if (form.assignee_type === 'agent' && !form.agent_profile_id) {
      setError('Elige el agente que ejecutará la tarea.')
      return
    }
    try {
      await onSave({
        title: form.title.trim(),
        description: form.description.trim() || null,
        status: form.status,
        assignee_type: form.assignee_type,
        agent_profile_id: form.assignee_type === 'agent' ? form.agent_profile_id : null,
        scheduled_at: datetimeLocalToIso(form.scheduled_at),
        due_at: datetimeLocalToIso(form.due_at),
        priority: form.priority,
      })
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const setField = (key: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [key]: value }))
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className="space-y-4">
      <div className="form-group">
        <label htmlFor="task-title" className="form-label">
          Título <span className="text-red-500">*</span>
        </label>
        <input
          id="task-title"
          className="input-field"
          value={form.title}
          onChange={(e) => setField('title', e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="task-description" className="form-label">
          Descripción
        </label>
        <textarea
          id="task-description"
          className="input-field min-h-[6rem]"
          value={form.description}
          onChange={(e) => setField('description', e.target.value)}
          placeholder="Qué hay que hacer. Si es para un agente, sé concreto: el agente no podrá preguntarte."
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="form-group">
          <label className="form-label" htmlFor="task-assignee">
            Asignada a
          </label>
          <ThemedSelect
            id="task-assignee"
            value={form.assignee_type}
            onChange={(v) => setField('assignee_type', v)}
            allowEmpty={false}
            options={[
              { value: 'user', label: 'Tú (manual)' },
              { value: 'agent', label: 'Un agente' },
            ]}
          />
        </div>
        {form.assignee_type === 'agent' && (
          <div className="form-group">
            <label className="form-label" htmlFor="task-agent">
              Agente
            </label>
            <ThemedSelect
              id="task-agent"
              value={form.agent_profile_id}
              onChange={(v) => setField('agent_profile_id', v)}
              options={agentOptions}
              placeholder="Elige un agente"
            />
          </div>
        )}
        <div className="form-group">
          <label className="form-label" htmlFor="task-priority">
            Prioridad
          </label>
          <ThemedSelect
            id="task-priority"
            value={form.priority}
            onChange={(v) => setField('priority', v)}
            allowEmpty={false}
            options={Object.entries(TASK_PRIORITY_LABELS).map(([value, label]) => ({ value, label }))}
          />
        </div>
        {task && (
          <div className="form-group">
            <label className="form-label" htmlFor="task-status">
              Estado
            </label>
            <ThemedSelect
              id="task-status"
              value={form.status}
              onChange={(v) => setField('status', v)}
              allowEmpty={false}
              options={Object.entries(TASK_STATUS_LABELS).map(([value, label]) => ({ value, label }))}
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="form-group">
          <label htmlFor="task-scheduled" className="form-label">
            Inicio / ejecución
          </label>
          <input
            id="task-scheduled"
            type="datetime-local"
            className="input-field"
            value={form.scheduled_at}
            onChange={(e) => setField('scheduled_at', e.target.value)}
          />
          {form.assignee_type === 'agent' && (
            <p className="text-xs text-text-muted mt-1">
              El agente ejecutará a esta hora aunque no estés en sesión (hora de Ciudad de México).
            </p>
          )}
        </div>
        <div className="form-group">
          <label htmlFor="task-due" className="form-label">
            Fecha límite
          </label>
          <input
            id="task-due"
            type="datetime-local"
            className="input-field"
            value={form.due_at}
            onChange={(e) => setField('due_at', e.target.value)}
          />
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {!hideActions && (
        <div className="flex flex-wrap justify-end gap-2 pt-2">
          {onCancel && (
            <button type="button" className="btn-secondary" onClick={onCancel} disabled={isSaving}>
              Cancelar
            </button>
          )}
          <button type="submit" className="btn-primary" disabled={isSaving}>
            {isSaving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      )}
    </form>
  )
}
