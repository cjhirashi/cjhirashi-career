import { apiClient } from './client'
import { Project } from '@/types'

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/public/projects')
    return response.data
  },

  getProjectById: async (id: number): Promise<Project> => {
    const response = await apiClient.get<Project>(`/public/projects/${id}`)
    return response.data
  },
}
