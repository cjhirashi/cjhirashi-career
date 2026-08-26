import React, { useEffect, useMemo, useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { ThemedSelect } from '@/components/ThemedSelect'
import { ThemedSwitch } from '@/components/ThemedSwitch'
import { SelectOption } from '@/config/careerResources'
import { useAuthStore } from '@/stores/authStore'
import { BedrockAgentCatalogItem, BedrockTask, BedrockTaskPayload } from '@/types/bedrock'
import { getErrorMessage } from '@/utils/errors'
import { datetimeLocalToIso, isoToDatetimeLocal, TASK_PRIORITY_LABELS, TASK_STATUS_LABELS } from './taskUtils'

export const TASK_FORM_ID = 'task-record-form'

interface TaskFormProps {
  task: BedrockTask | null
  subtasks?: BedrockTask[]
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

interface SubtaskDraft {
  key: string
  id?: string
  title: string
  assignee_type: string
  agent_profile_id: string
  is_blocking: boolean
  execute_on_turn: boolean
  scheduled_at: string
  due_at: string
  priority: string
}

const emptySubtask = (): SubtaskDraft => ({
  key: `new-${Math.random().toString(36).slice(2, 8)}`,
  title: '',
  assignee_type: 'user',
  agent_profile_id: '',
  is_blocking: true,
  execute_on_turn: false,
  scheduled_at: '',
  due_at: '',
  priority: 'medium',
})

const toDraft = (task: BedrockTask): SubtaskDraft => ({
  key: task.id,
  id: task.id,
  title: task.title,
  assignee_type: task.assignee_type === 'agent' ? 'agent' : 'user',
  agent_profile_id: task.agent_profile_id ?? '',
  is_blocking: task.is_blocking !== false,
  execute_on_turn: Boolean(task.execute_on_turn),
  scheduled_at: isoToDatetimeLocal(task.scheduled_at),
  due_at: isoToDatetimeLocal(task.due_at),
  priority: task.priority || 'medium',
})

export const TaskForm: React.FC<TaskFormProps> = ({
  task,
  subtasks = [],
  agents,
  onSave,
  isSaving,
  formId = TASK_FORM_ID,
  hideActions = false,
  onCancel,
}) => {
  const [form, setForm] = useState(emptyForm)
  const [drafts, setDrafts] = useState<SubtaskDraft[]>([])
  const [error, setError] = useState<string | null>(null)
  const isChild = Boolean(task?.parent_id)
  const user = useAuthStore((state) => state.user)
  const userName = user?.full_name?.trim() || user?.username || 'Usuario'

  useEffect(() => {
    if (!task) {
      setForm(emptyForm)
      setDrafts([])
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
    setDrafts(isChild ? [] : subtasks.map(toDraft))
    setError(null)
  }, [task, subtasks, isChild])

  const responsableOptions = useMemo<SelectOption[]>(
    () => [
      { value: 'user', label: userName, imageUrl: user?.photo_url ?? null },
      ...[...agents]
        .sort((a, b) => a.level - b.level || a.label.localeCompare(b.label))
        .map((agent) => ({
          value: agent.profile_id,
          label: agent.label,
          imageUrl: agent.photo_url ?? null,
        })),
    ],
    [agents, userName, user?.photo_url]
  )

  const applyResponsable = (value: string): { assignee_type: string; agent_profile_id: string } =>
    value === 'user' || !value
      ? { assignee_type: 'user', agent_profile_id: '' }
      : { assignee_type: 'agent', agent_profile_id: value }

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
    const nested = drafts.filter((row) => row.title.trim())
    for (const row of nested) {
      if (row.assignee_type === 'agent' && !row.agent_profile_id) {
        setError(`La subtarea "${row.title.trim()}" necesita un agente.`)
        return
      }
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
        ...(isChild
          ? {}
          : {
              subtasks: nested.map((row, index) => ({
                id: row.id,
                title: row.title.trim(),
                assignee_type: row.assignee_type,
                agent_profile_id: row.assignee_type === 'agent' ? row.agent_profile_id : null,
                is_blocking: row.is_blocking,
                execute_on_turn: row.assignee_type === 'agent' ? row.execute_on_turn : false,
                scheduled_at: datetimeLocalToIso(row.scheduled_at),
                due_at: datetimeLocalToIso(row.due_at),
                priority: row.priority,
                sort_order: index,
              })),
            }),
      })
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const setField = (key: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const setDraft = (key: string, patch: Partial<SubtaskDraft>) => {
    setDrafts((current) => current.map((row) => (row.key === key ? { ...row, ...patch } : row)))
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
            Responsable
          </label>
          <ThemedSelect
            id="task-assignee"
            value={form.assignee_type === 'agent' ? form.agent_profile_id : 'user'}
            onChange={(v) => {
              const next = applyResponsable(v)
              setForm((current) => ({ ...current, ...next }))
            }}
            allowEmpty={false}
            options={responsableOptions}
          />
        </div>
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
              Si no usas “al turno”, el agente ejecuta a esta hora (Ciudad de México) aunque no estés en sesión.
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

      {!isChild && (
        <div className="space-y-3 pt-2 border-t border-border">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide">Subtareas</h3>
            <button
              type="button"
              className="btn-icon btn-icon-sm"
              aria-label="Añadir subtarea"
              title="Añadir subtarea"
              onClick={() => setDrafts((current) => [...current, emptySubtask()])}
            >
              <Plus size={13} />
            </button>
          </div>
          <p className="text-xs text-text-muted">
            El responsable de arriba orquesta el plan. Cada subtarea puede ir a {userName} o a un agente, ser
            bloqueante (las siguientes esperan) y ejecutarse a una hora o cuando le toque el turno.
          </p>
          {drafts.length === 0 && (
            <p className="text-sm text-text-secondary">Sin subtareas. El padre se ejecuta como una tarea suelta.</p>
          )}
          {drafts.map((row, index) => (
            <div key={row.key} className="rounded-xl border border-border bg-glass/40 p-3 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-text-secondary">Paso {index + 1}</span>
                <button
                  type="button"
                  className="p-1 rounded-lg text-text-muted hover:text-red-500"
                  aria-label={`Quitar subtarea ${index + 1}`}
                  onClick={() => setDrafts((current) => current.filter((item) => item.key !== row.key))}
                >
                  <Trash2 size={13} />
                </button>
              </div>
              <input
                className="input-field"
                value={row.title}
                onChange={(e) => setDraft(row.key, { title: e.target.value })}
                placeholder="Título de la subtarea"
                aria-label={`Título de subtarea ${index + 1}`}
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <ThemedSelect
                  value={row.assignee_type === 'agent' ? row.agent_profile_id : 'user'}
                  onChange={(v) => {
                    const next = applyResponsable(v)
                    setDraft(row.key, {
                      ...next,
                      execute_on_turn: next.assignee_type === 'agent' ? row.execute_on_turn : false,
                    })
                  }}
                  allowEmpty={false}
                  aria-label={`Responsable de subtarea ${index + 1}`}
                  options={responsableOptions}
                />
                <input
                  type="datetime-local"
                  className="input-field"
                  value={row.scheduled_at}
                  onChange={(e) => setDraft(row.key, { scheduled_at: e.target.value })}
                  aria-label={`Inicio de subtarea ${index + 1}`}
                />
                <input
                  type="datetime-local"
                  className="input-field"
                  value={row.due_at}
                  onChange={(e) => setDraft(row.key, { due_at: e.target.value })}
                  aria-label={`Límite de subtarea ${index + 1}`}
                />
              </div>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 text-sm text-text">
                  <ThemedSwitch
                    checked={row.is_blocking}
                    onChange={(checked) => setDraft(row.key, { is_blocking: checked })}
                    aria-label={`Bloqueante subtarea ${index + 1}`}
                  />
                  Bloqueante
                </label>
                {row.assignee_type === 'agent' && (
                  <label className="flex items-center gap-2 text-sm text-text">
                    <ThemedSwitch
                      checked={row.execute_on_turn}
                      onChange={(checked) => setDraft(row.key, { execute_on_turn: checked })}
                      aria-label={`Ejecutar al turno subtarea ${index + 1}`}
                    />
                    Ejecutar al turno
                  </label>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

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
