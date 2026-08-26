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

export function isRootTask(task: BedrockTask): boolean {
  return !task.parent_id
}

export function groupSubtasks(tasks: BedrockTask[]): Map<string, BedrockTask[]> {
  const grouped = new Map<string, BedrockTask[]>()
  for (const task of tasks) {
    if (!task.parent_id) continue
    const list = grouped.get(task.parent_id) ?? []
    list.push(task)
    grouped.set(task.parent_id, list)
  }
  for (const list of grouped.values()) {
    list.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.id.localeCompare(b.id))
  }
  return grouped
}

export function isTaskBlocked(task: BedrockTask, siblings: BedrockTask[]): boolean {
  if (!task.parent_id) return false
  const ordered = [...siblings].sort(
    (a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.id.localeCompare(b.id)
  )
  for (const sibling of ordered) {
    if (sibling.id === task.id) return false
    if (sibling.is_blocking && sibling.status !== 'done' && sibling.status !== 'cancelled') {
      return true
    }
  }
  return false
}

export interface AssigneeContext {
  userName: string
  userPhoto: string | null
  agentLabels: Record<string, string>
  agentPhotos: Record<string, string | null>
}

export function assigneeDisplay(
  task: BedrockTask,
  ctx: AssigneeContext
): { name: string; imageUrl: string | null } {
  if (task.assignee_type === 'agent') {
    const profileId = task.agent_profile_id ?? ''
    return {
      name: (profileId && ctx.agentLabels[profileId]) || profileId || 'Agente',
      imageUrl: (profileId && ctx.agentPhotos[profileId]) || null,
    }
  }
  return { name: ctx.userName, imageUrl: ctx.userPhoto }
}

export function assigneeLabel(task: BedrockTask, ctx: AssigneeContext): string {
  return assigneeDisplay(task, ctx).name
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
