import { apiClient } from './client'
import { Project } from '@/types'

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/public/projects')
    return response.data
  },

  getProjectBySlug: async (slug: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/public/projects/${slug}`)
    return response.data
  },
}
