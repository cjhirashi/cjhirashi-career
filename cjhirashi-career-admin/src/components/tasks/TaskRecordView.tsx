import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Bot, Lock, User } from 'lucide-react'
import { MarkdownTable } from '@/components/MarkdownTable'
import { ThemedSelect } from '@/components/ThemedSelect'
import { BedrockTask, TaskStatus } from '@/types/bedrock'
import { formatDateTime } from '@/utils/formatters'
import {
  assigneeLabel,
  isTaskBlocked,
  TASK_PRIORITY_LABELS,
  TASK_STATUS_LABELS,
} from './taskUtils'

interface TaskRecordViewProps {
  task: BedrockTask
  subtasks?: BedrockTask[]
  agentLabels: Record<string, string>
  onStatus: (task: BedrockTask, status: TaskStatus) => void
  onOpenSubtask?: (task: BedrockTask) => void
}

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

const StatusSelect: React.FC<{
  task: BedrockTask
  onStatus: (task: BedrockTask, status: TaskStatus) => void
}> = ({ task, onStatus }) => (
  <ThemedSelect
    id={`task-status-${task.id}`}
    value={task.status}
    onChange={(value) => onStatus(task, value as TaskStatus)}
    allowEmpty={false}
    aria-label={`Estado de ${task.title}`}
    options={Object.entries(TASK_STATUS_LABELS).map(([value, label]) => ({ value, label }))}
  />
)

export const TaskRecordView: React.FC<TaskRecordViewProps> = ({
  task,
  subtasks = [],
  agentLabels,
  onStatus,
  onOpenSubtask,
}) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Información</h3>
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Título">{task.title}</Field>
        <Field label="Estado">
          <StatusSelect task={task} onStatus={onStatus} />
        </Field>
        <Field label="Responsable">
          <span className="inline-flex items-center gap-1.5">
            {task.assignee_type === 'agent' ? <Bot size={13} aria-hidden="true" /> : <User size={13} aria-hidden="true" />}
            {assigneeLabel(task, agentLabels)}
          </span>
        </Field>
        <Field label="Prioridad">{TASK_PRIORITY_LABELS[task.priority] ?? task.priority}</Field>
        <Field label="Inicio / ejecución">{task.scheduled_at ? formatDateTime(task.scheduled_at) : '—'}</Field>
        <Field label="Fecha límite">{task.due_at ? formatDateTime(task.due_at) : '—'}</Field>
        {task.parent_id && (
          <Field label="Plan">
            Subtarea {task.is_blocking !== false ? 'bloqueante' : 'no bloqueante'}
            {task.execute_on_turn ? ' · ejecuta al turno' : ''}
          </Field>
        )}
        <Field label="Descripción" wide>
          {task.description ? (
            <div className="markdown-body markdown-body-compact">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ table: MarkdownTable }}>
                {task.description}
              </ReactMarkdown>
            </div>
          ) : (
            '—'
          )}
        </Field>
        {task.notes && (
          <Field label="Notas" wide>
            <p className="whitespace-pre-wrap">{task.notes}</p>
          </Field>
        )}
      </dl>
    </div>

    {subtasks.length > 0 && (
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Subtareas</h3>
        <ul className="space-y-2">
          {subtasks.map((child, index) => {
            const blocked = isTaskBlocked(child, subtasks)
            return (
              <li
                key={child.id}
                className="rounded-xl border border-border bg-glass/30 p-3 grid grid-cols-1 md:grid-cols-[1fr_12rem] gap-3 items-center"
              >
                <div className="min-w-0">
                  <button
                    type="button"
                    className="text-sm font-medium text-text text-left hover:underline"
                    onClick={() => onOpenSubtask?.(child)}
                  >
                    {index + 1}. {child.title}
                  </button>
                  <p className="text-[11px] text-text-muted mt-0.5 inline-flex items-center gap-1.5 flex-wrap">
                    {child.assignee_type === 'agent' ? <Bot size={11} /> : <User size={11} />}
                    {assigneeLabel(child, agentLabels)}
                    {child.is_blocking !== false ? ' · bloqueante' : ' · no bloquea'}
                    {child.execute_on_turn ? ' · al turno' : ''}
                    {blocked && (
                      <span className="inline-flex items-center gap-1 text-amber-400">
                        <Lock size={11} aria-hidden="true" /> esperando paso anterior
                      </span>
                    )}
                  </p>
                </div>
                <StatusSelect task={child} onStatus={onStatus} />
              </li>
            )
          })}
        </ul>
      </div>
    )}

    {(task.execution_result || task.error_message || task.executed_at) && (
      <div>
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Ejecución</h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Ejecutada">{task.executed_at ? formatDateTime(task.executed_at) : '—'}</Field>
          {task.error_message && (
            <Field label="Error" wide>
              <p className="text-red-400 whitespace-pre-wrap">{task.error_message}</p>
            </Field>
          )}
          {task.execution_result && (
            <Field label="Resultado del agente" wide>
              <p className="whitespace-pre-wrap">{task.execution_result}</p>
            </Field>
          )}
        </dl>
      </div>
    )}

    <div className="pt-4 border-t border-border">
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Metadatos</h3>
      <dl className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Field label="ID">
          <span className="font-mono text-xs break-all">{task.id}</span>
        </Field>
        <Field label="Creado">{formatDateTime(task.created_at)}</Field>
        <Field label="Última actualización">{formatDateTime(task.updated_at)}</Field>
      </dl>
    </div>
  </div>
)
