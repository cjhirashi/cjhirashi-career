import { apiClient } from './client'
import { ContactContent } from '@/types'

export const contactApi = {
  getContact: async (): Promise<ContactContent> => {
    const response = await apiClient.get<ContactContent>('/public/contact')
    return response.data
  },
}
