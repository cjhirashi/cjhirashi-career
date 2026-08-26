import { apiClient } from './client'
import { AboutContent } from '@/types'

export const aboutApi = {
  getAbout: async (): Promise<AboutContent> => {
    const response = await apiClient.get<AboutContent>('/public/about')
    return response.data
  },
}
