import { axiosInstance } from './client'
import { Task, TaskPayload } from '@/types/tasks'

/**
 * Client for the task board (`/agent-tasks`). Same generic CRUD as career
 * tables, but not under `/career/*`.
 */
export const agentTasksApi = {
  list: async (): Promise<Task[]> => {
    const response = await axiosInstance.get<Task[]>('/agent-tasks', {
      params: { skip: 0, limit: 100, sort_by: 'scheduled_at', sort_dir: 'asc' },
    })
    return response.data
  },

  count: async (): Promise<number> => {
    const response = await axiosInstance.get<{ count: number }>('/agent-tasks/count')
    return response.data.count
  },

  create: async (payload: TaskPayload & { title: string }): Promise<Task> => {
    const response = await axiosInstance.post<Task>('/agent-tasks', payload)
    return response.data
  },

  update: async (id: string, payload: TaskPayload): Promise<Task> => {
    const response = await axiosInstance.put<Task>(`/agent-tasks/${id}`, payload)
    return response.data
  },

  remove: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/agent-tasks/${id}`)
  },
}
