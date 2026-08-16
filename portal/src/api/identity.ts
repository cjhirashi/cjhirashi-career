import { apiClient } from './client'
import { Identity } from '@/types'

export const identityApi = {
  getIdentity: async (): Promise<Identity> => {
    const response = await apiClient.get<Identity>('/identity')
    return response.data
  },

  getCompetencies: async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>('/competencies')
    return response.data
  },
}
