import { apiClient } from './client'
import { Project } from '@/types'

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/evidence')
    return response.data
  },

  getProjectById: async (id: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/evidence/${id}`)
    return response.data
  },

  getFeaturedProjects: async (limit: number = 3): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>(`/evidence?featured=true&limit=${limit}`)
    return response.data
  },
}
