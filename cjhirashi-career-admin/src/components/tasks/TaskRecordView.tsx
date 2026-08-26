import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Bot, User } from 'lucide-react'
import { MarkdownTable } from '@/components/MarkdownTable'
import { BedrockTask } from '@/types/bedrock'
import { formatDateTime } from '@/utils/formatters'
import { assigneeLabel, statusChipClass, TASK_PRIORITY_LABELS, TASK_STATUS_LABELS } from './taskUtils'

interface TaskRecordViewProps {
  task: BedrockTask
  agentLabels: Record<string, string>
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

export const TaskRecordView: React.FC<TaskRecordViewProps> = ({ task, agentLabels }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Información</h3>
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Título">{task.title}</Field>
        <Field label="Estado">
          <span className={`inline-flex px-2 py-0.5 rounded-lg text-xs font-medium ${statusChipClass(task.status)}`}>
            {TASK_STATUS_LABELS[task.status] ?? task.status}
          </span>
        </Field>
        <Field label="Asignada a">
          <span className="inline-flex items-center gap-1.5">
            {task.assignee_type === 'agent' ? <Bot size={13} aria-hidden="true" /> : <User size={13} aria-hidden="true" />}
            {assigneeLabel(task, agentLabels)}
          </span>
        </Field>
        <Field label="Prioridad">{TASK_PRIORITY_LABELS[task.priority] ?? task.priority}</Field>
        <Field label="Inicio / ejecución">{task.scheduled_at ? formatDateTime(task.scheduled_at) : '—'}</Field>
        <Field label="Fecha límite">{task.due_at ? formatDateTime(task.due_at) : '—'}</Field>
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
