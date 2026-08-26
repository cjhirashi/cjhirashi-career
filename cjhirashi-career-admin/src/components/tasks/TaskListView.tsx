import React from 'react'
import { Bot, Play, Trash2, User } from 'lucide-react'
import { BedrockTask } from '@/types/bedrock'
import { formatDateTime } from '@/utils/formatters'
import {
  assigneeLabel,
  canRunAgentTask,
  statusChipClass,
  TASK_PRIORITY_LABELS,
  TASK_STATUS_LABELS,
} from './taskUtils'

interface TaskListViewProps {
  tasks: BedrockTask[]
  agentLabels: Record<string, string>
  onOpen: (task: BedrockTask) => void
  onDelete: (task: BedrockTask) => void
  onRun: (task: BedrockTask) => void
  runningId?: string
}

export const TaskListView: React.FC<TaskListViewProps> = ({
  tasks,
  agentLabels,
  onOpen,
  onDelete,
  onRun,
  runningId,
}) => (
  <div className="overflow-x-auto">
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs uppercase tracking-wide text-text-secondary border-b border-border">
          <th className="py-2 pr-3 font-semibold">Tarea</th>
          <th className="py-2 pr-3 font-semibold">Asignada a</th>
          <th className="py-2 pr-3 font-semibold">Estado</th>
          <th className="py-2 pr-3 font-semibold">Inicio</th>
          <th className="py-2 pr-3 font-semibold">Límite</th>
          <th className="py-2 pr-3 font-semibold">Prioridad</th>
          <th className="py-2 font-semibold text-right"> </th>
        </tr>
      </thead>
      <tbody>
        {tasks.map((task) => (
          <tr
            key={task.id}
            className="border-b border-border/60 hover:bg-glass/40 cursor-pointer"
            onClick={() => onOpen(task)}
          >
            <td className="py-2.5 pr-3 font-medium text-text">{task.title}</td>
            <td className="py-2.5 pr-3 text-text-secondary">
              <span className="inline-flex items-center gap-1.5">
                {task.assignee_type === 'agent' ? <Bot size={13} aria-hidden="true" /> : <User size={13} aria-hidden="true" />}
                {assigneeLabel(task, agentLabels)}
              </span>
            </td>
            <td className="py-2.5 pr-3">
              <span className={`inline-flex px-2 py-0.5 rounded-lg text-xs font-medium ${statusChipClass(task.status)}`}>
                {TASK_STATUS_LABELS[task.status] ?? task.status}
              </span>
            </td>
            <td className="py-2.5 pr-3 text-text-secondary whitespace-nowrap">
              {task.scheduled_at ? formatDateTime(task.scheduled_at) : '—'}
            </td>
            <td className="py-2.5 pr-3 text-text-secondary whitespace-nowrap">
              {task.due_at ? formatDateTime(task.due_at) : '—'}
            </td>
            <td className="py-2.5 pr-3 text-text-secondary">
              {TASK_PRIORITY_LABELS[task.priority] ?? task.priority}
            </td>
            <td className="py-2.5 text-right whitespace-nowrap" onClick={(event) => event.stopPropagation()}>
              {canRunAgentTask(task) && (
                <button
                  type="button"
                  className="p-1 rounded-lg text-text-muted hover:bg-glass hover:text-cyan-400"
                  aria-label={`Ejecutar "${task.title}"`}
                  title="Ejecutar ahora"
                  disabled={runningId === task.id}
                  onClick={() => onRun(task)}
                >
                  <Play size={13} aria-hidden="true" />
                </button>
              )}
              <button
                type="button"
                className="p-1 rounded-lg text-text-muted hover:bg-glass hover:text-red-500"
                aria-label={`Eliminar "${task.title}"`}
                title="Eliminar"
                onClick={() => onDelete(task)}
              >
                <Trash2 size={13} aria-hidden="true" />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)
