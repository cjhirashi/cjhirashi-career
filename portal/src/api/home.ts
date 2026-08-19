import { apiClient } from './client'
import { HomeContent } from '@/types'

export const homeApi = {
  getHome: async (): Promise<HomeContent> => {
    const response = await apiClient.get<HomeContent>('/public/home')
    return response.data
  },
}
