export type TaskStatus = 'pending' | 'in_progress' | 'done' | 'cancelled' | 'failed'
export type TaskAssigneeType = 'user' | 'agent'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface Task {
  id: string
  user_id: string
  title: string
  description: string | null
  status: TaskStatus | string
  notes: string | null
  assignee_type: TaskAssigneeType | string
  scheduled_at: string | null
  due_at: string | null
  priority: TaskPriority | string
  parent_id: string | null
  sort_order: number
  is_blocking: boolean
  execute_on_turn: boolean
  turn_notified_at?: string | null
  execution_result: string | null
  executed_at: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export type TaskPayload = Partial<{
  title: string
  description: string | null
  status: string
  notes: string | null
  assignee_type: string
  scheduled_at: string | null
  due_at: string | null
  priority: string
  parent_id: string | null
  sort_order: number
  is_blocking: boolean
  execute_on_turn: boolean
  subtasks: TaskPayload[]
}>
