import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Trash2 } from 'lucide-react'
import { ThemedSelect } from '@/components/ThemedSelect'
import { MarkdownTable } from '@/components/MarkdownTable'
import { BedrockTask, TaskStatus } from '@/types/bedrock'
import { assigneeLabel, TASK_STATUS_COLUMNS, TASK_STATUS_LABELS } from './taskUtils'

interface TaskKanbanViewProps {
  tasks: BedrockTask[]
  agentLabels: Record<string, string>
  onOpen: (task: BedrockTask) => void
  onStatus: (task: BedrockTask, status: TaskStatus) => void
  onDelete: (task: BedrockTask) => void
}

export const TaskKanbanView: React.FC<TaskKanbanViewProps> = ({
  tasks,
  agentLabels,
  onOpen,
  onStatus,
  onDelete,
}) => (
  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
    {TASK_STATUS_COLUMNS.map((status) => {
      const columnTasks = tasks.filter((task) => task.status === status)
      return (
        <div key={status} className="space-y-2 min-w-0">
          <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wide px-1">
            {TASK_STATUS_LABELS[status] ?? status} · {columnTasks.length}
          </h2>
          {columnTasks.map((task) => (
            <div key={task.id} className="card">
              <div className="card-body space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <button
                    type="button"
                    className="text-sm font-medium text-text text-left hover:underline"
                    onClick={() => onOpen(task)}
                  >
                    {task.title}
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(task)}
                    aria-label={`Eliminar "${task.title}"`}
                    title="Eliminar"
                    className="p-1 rounded-lg text-text-muted hover:bg-glass hover:text-red-500 transition-colors flex-shrink-0"
                  >
                    <Trash2 size={13} aria-hidden="true" />
                  </button>
                </div>
                <p className="text-[11px] text-text-muted">{assigneeLabel(task, agentLabels)}</p>
                {task.description && (
                  <div className="markdown-body markdown-body-compact text-xs">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ table: MarkdownTable }}>
                      {task.description}
                    </ReactMarkdown>
                  </div>
                )}
                <ThemedSelect
                  value={task.status}
                  onChange={(v) => onStatus(task, v as TaskStatus)}
                  className="text-xs"
                  aria-label={`Estado de "${task.title}"`}
                  allowEmpty={false}
                  options={TASK_STATUS_COLUMNS.map((item) => ({
                    value: item,
                    label: TASK_STATUS_LABELS[item],
                  }))}
                />
              </div>
            </div>
          ))}
        </div>
      )
    })}
  </div>
)
