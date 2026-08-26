import { axiosInstance } from './client'
import { BedrockTask, BedrockTaskPayload } from '@/types/bedrock'

/**
 * Client for the task board (`/agent-tasks`). Same generic CRUD as career
 * tables, but not under `/career/*`. `run` triggers the API scheduler's
 * harness so an assigned agent executes without an open Admin session.
 */
export const agentTasksApi = {
  list: async (): Promise<BedrockTask[]> => {
    const response = await axiosInstance.get<BedrockTask[]>('/agent-tasks', {
      params: { skip: 0, limit: 100, sort_by: 'scheduled_at', sort_dir: 'asc' },
    })
    return response.data
  },

  count: async (): Promise<number> => {
    const response = await axiosInstance.get<{ count: number }>('/agent-tasks/count')
    return response.data.count
  },

  create: async (payload: BedrockTaskPayload & { title: string }): Promise<BedrockTask> => {
    const response = await axiosInstance.post<BedrockTask>('/agent-tasks', payload)
    return response.data
  },

  update: async (id: string, payload: BedrockTaskPayload): Promise<BedrockTask> => {
    const response = await axiosInstance.put<BedrockTask>(`/agent-tasks/${id}`, payload)
    return response.data
  },

  remove: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/agent-tasks/${id}`)
  },

  run: async (id: string): Promise<BedrockTask> => {
    const response = await axiosInstance.post<BedrockTask>(`/agent-tasks/${id}/run`)
    return response.data
  },
}
