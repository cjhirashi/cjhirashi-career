import React, { useMemo } from 'react'
import { addDays, differenceInCalendarDays, format, max, min, startOfDay } from 'date-fns'
import { es } from 'date-fns/locale'
import { BedrockTask } from '@/types/bedrock'
import { assigneeDisplay, AssigneeContext, priorityBarClass, taskEndDate, taskStartDate } from './taskUtils'

interface TaskGanttViewProps {
  tasks: BedrockTask[]
  assignees: AssigneeContext
  onOpen: (task: BedrockTask) => void
}

export const TaskGanttView: React.FC<TaskGanttViewProps> = ({ tasks, assignees, onOpen }) => {
  const dated = useMemo(
    () =>
      tasks
        .map((task) => {
          const start = taskStartDate(task)
          const end = taskEndDate(task)
          if (!start) return null
          const startDay = startOfDay(start)
          const endDay = startOfDay(end ?? addDays(start, 1))
          return { task, start: startDay, end: endDay < startDay ? addDays(startDay, 1) : endDay }
        })
        .filter((row): row is { task: BedrockTask; start: Date; end: Date } => row !== null),
    [tasks]
  )

  const range = useMemo(() => {
    const today = startOfDay(new Date())
    if (dated.length === 0) {
      return { start: today, days: 14 }
    }
    const start = min(dated.map((row) => row.start))
    const end = max(dated.map((row) => row.end))
    return { start, days: Math.max(7, differenceInCalendarDays(end, start) + 1) }
  }, [dated])

  if (dated.length === 0) {
    return (
      <p className="text-sm text-text-secondary">
        El Gantt aparece cuando una tarea tiene fecha de inicio o límite.
      </p>
    )
  }

  const ticks = Array.from({ length: range.days }, (_, index) => addDays(range.start, index))

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[40rem]">
        <div className="flex border-b border-border pb-2 mb-2">
          <div className="w-48 shrink-0" />
          <div className="flex-1 flex">
            {ticks.map((day) => (
              <div key={day.toISOString()} className="flex-1 text-[10px] text-text-muted text-center">
                {format(day, 'd', { locale: es })}
                <span className="block capitalize">{format(day, 'EEE', { locale: es })}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          {dated.map(({ task, start, end }) => {
            const offset = differenceInCalendarDays(start, range.start)
            const span = Math.max(1, differenceInCalendarDays(end, start))
            return (
              <div key={task.id} className="flex items-center gap-0">
                <button
                  type="button"
                  className="w-48 shrink-0 text-left text-xs text-text truncate pr-3 hover:underline"
                  onClick={() => onOpen(task)}
                  title={task.title}
                >
                  {task.title}
                  <span className="block text-[10px] text-text-muted truncate">
                    {assigneeDisplay(task, assignees).name}
                  </span>
                </button>
                <div className="flex-1 relative h-8 rounded-md bg-glass/40">
                  <button
                    type="button"
                    onClick={() => onOpen(task)}
                    className={`absolute top-1 h-6 rounded-md ${priorityBarClass(task.priority)} opacity-85 hover:opacity-100`}
                    style={{
                      left: `${(offset / range.days) * 100}%`,
                      width: `${(span / range.days) * 100}%`,
                      minWidth: '0.75rem',
                    }}
                    aria-label={task.title}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
