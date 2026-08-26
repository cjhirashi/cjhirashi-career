import React, { useMemo, useState } from 'react'
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameMonth,
  startOfMonth,
  startOfWeek,
} from 'date-fns'
import { es } from 'date-fns/locale'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { BedrockTask } from '@/types/bedrock'
import { statusChipClass, taskStartDate } from './taskUtils'

interface TaskCalendarViewProps {
  tasks: BedrockTask[]
  onOpen: (task: BedrockTask) => void
}

const WEEKDAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

export const TaskCalendarView: React.FC<TaskCalendarViewProps> = ({ tasks, onOpen }) => {
  const [cursor, setCursor] = useState(() => new Date())

  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(cursor), { weekStartsOn: 1 })
    const end = endOfWeek(endOfMonth(cursor), { weekStartsOn: 1 })
    return eachDayOfInterval({ start, end })
  }, [cursor])

  const tasksByDay = useMemo(() => {
    const map = new Map<string, BedrockTask[]>()
    for (const task of tasks) {
      const start = taskStartDate(task)
      if (!start) continue
      const key = format(start, 'yyyy-MM-dd')
      const list = map.get(key) ?? []
      list.push(task)
      map.set(key, list)
    }
    return map
  }, [tasks])

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text capitalize">
          {format(cursor, 'MMMM yyyy', { locale: es })}
        </h2>
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="btn-secondary btn-small"
            aria-label="Mes anterior"
            onClick={() => setCursor((current) => addMonths(current, -1))}
          >
            <ChevronLeft size={16} aria-hidden="true" />
          </button>
          <button type="button" className="btn-secondary btn-small" onClick={() => setCursor(new Date())}>
            Hoy
          </button>
          <button
            type="button"
            className="btn-secondary btn-small"
            aria-label="Mes siguiente"
            onClick={() => setCursor((current) => addMonths(current, 1))}
          >
            <ChevronRight size={16} aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-px rounded-xl overflow-hidden border border-border bg-border">
        {WEEKDAYS.map((label) => (
          <div key={label} className="bg-glass px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
            {label}
          </div>
        ))}
        {days.map((day) => {
          const key = format(day, 'yyyy-MM-dd')
          const dayTasks = tasksByDay.get(key) ?? []
          const inMonth = isSameMonth(day, cursor)
          return (
            <div
              key={key}
              className={`min-h-[7.5rem] bg-[var(--bg-card)] p-1.5 ${inMonth ? '' : 'opacity-40'}`}
            >
              <p className="text-xs text-text-secondary mb-1">{format(day, 'd')}</p>
              <div className="space-y-1">
                {dayTasks.slice(0, 3).map((task) => (
                  <button
                    key={task.id}
                    type="button"
                    onClick={() => onOpen(task)}
                    className={`block w-full truncate rounded-md px-1.5 py-0.5 text-left text-[11px] ${statusChipClass(task.status)}`}
                    title={task.title}
                  >
                    {task.title}
                  </button>
                ))}
                {dayTasks.length > 3 && (
                  <p className="text-[10px] text-text-muted px-1">+{dayTasks.length - 3} más</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
