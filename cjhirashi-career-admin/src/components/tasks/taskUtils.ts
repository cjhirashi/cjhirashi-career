import { addDays, format, parseISO, startOfDay } from 'date-fns'
import { es } from 'date-fns/locale'
import { BedrockTask, TaskStatus } from '@/types/bedrock'

export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  in_progress: 'En progreso',
  done: 'Hecha',
  cancelled: 'Cancelada',
  failed: 'Fallida',
}

export const TASK_STATUS_COLUMNS: TaskStatus[] = [
  'pending',
  'in_progress',
  'done',
  'failed',
  'cancelled',
]

export const TASK_PRIORITY_LABELS: Record<string, string> = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
}

const MEXICO_CITY_TZ = 'America/Mexico_City'

export function isoToDatetimeLocal(iso: string | null | undefined): string {
  if (!iso) return ''
  try {
    const date = typeof iso === 'string' ? parseISO(iso) : iso
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: MEXICO_CITY_TZ,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).formatToParts(date)
    const get = (type: string) => parts.find((part) => part.type === type)?.value ?? ''
    return `${get('year')}-${get('month')}-${get('day')}T${get('hour')}:${get('minute')}`
  } catch {
    return ''
  }
}

/** Interprets a `datetime-local` value as America/Mexico_City (UTC-6, no DST). */
export function datetimeLocalToIso(value: string): string | null {
  if (!value.trim()) return null
  const iso = new Date(`${value}:00-06:00`).toISOString()
  return iso
}

export function taskStartIso(task: BedrockTask): string | null {
  return task.scheduled_at || task.due_at || null
}

export function taskStartDate(task: BedrockTask): Date | null {
  const iso = taskStartIso(task)
  if (!iso) return null
  try {
    return parseISO(iso)
  } catch {
    return null
  }
}

export function taskEndDate(task: BedrockTask): Date | null {
  if (task.due_at) {
    try {
      return parseISO(task.due_at)
    } catch {
      return null
    }
  }
  const start = taskStartDate(task)
  return start ? addDays(start, 1) : null
}

export function canRunAgentTask(task: BedrockTask): boolean {
  return (
    task.assignee_type === 'agent' &&
    Boolean(task.agent_profile_id) &&
    (task.status === 'pending' || task.status === 'failed')
  )
}

export function assigneeLabel(
  task: BedrockTask,
  agentLabels: Record<string, string>
): string {
  if (task.assignee_type === 'agent') {
    if (!task.agent_profile_id) return 'Agente'
    return agentLabels[task.agent_profile_id] ?? task.agent_profile_id
  }
  return 'Tú'
}

export function statusChipClass(status: string): string {
  switch (status) {
    case 'done':
      return 'bg-emerald-500/15 text-emerald-300'
    case 'in_progress':
      return 'bg-sky-500/15 text-sky-300'
    case 'failed':
      return 'bg-red-500/15 text-red-300'
    case 'cancelled':
      return 'bg-slate-500/15 text-slate-400'
    default:
      return 'bg-amber-500/15 text-amber-300'
  }
}

export function priorityBarClass(priority: string): string {
  switch (priority) {
    case 'high':
      return 'bg-red-400'
    case 'low':
      return 'bg-slate-500'
    default:
      return 'bg-cyan-400'
  }
}

export function formatDayHeading(date: Date): string {
  return format(date, "EEEE d 'de' MMMM", { locale: es })
}

export function sameDay(a: Date, b: Date): boolean {
  return startOfDay(a).getTime() === startOfDay(b).getTime()
}
