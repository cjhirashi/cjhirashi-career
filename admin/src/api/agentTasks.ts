import { axiosInstance } from './client'
import { BedrockTask } from '@/types/bedrock'

/**
 * Client for the agent's task/plan tracker (`/agent-tasks`) - a real REST
 * CRUD resource built on the same generic router every career-domain table
 * uses (see api/src/routes/bedrock_tasks.py), just not nested under
 * `/career/*` like careerApi's resources are, so it gets its own thin
 * client instead of reusing careerApi's hardcoded base path.
 */
export const agentTasksApi = {
  list: async (): Promise<BedrockTask[]> => {
    const response = await axiosInstance.get<BedrockTask[]>('/agent-tasks')
    return response.data
  },

  create: async (payload: { title: string; description?: string; status?: string }): Promise<BedrockTask> => {
    const response = await axiosInstance.post<BedrockTask>('/agent-tasks', payload)
    return response.data
  },

  update: async (id: string, payload: Partial<{ title: string; description: string; status: string }>): Promise<BedrockTask> => {
    const response = await axiosInstance.put<BedrockTask>(`/agent-tasks/${id}`, payload)
    return response.data
  },

  remove: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/agent-tasks/${id}`)
  },
}
