import { apiClient } from './client'
import { ContactContent } from '@/types'

interface SendMessagePayload {
  name: string
  email: string
  message: string
  website?: string
}

interface SendMessageResponse {
  id: string
}

export const contactApi = {
  getContact: async (): Promise<ContactContent> => {
    const response = await apiClient.get<ContactContent>('/public/contact')
    return response.data
  },

  sendMessage: async (payload: SendMessagePayload): Promise<SendMessageResponse> => {
    const response = await apiClient.post<SendMessageResponse>('/public/contact-message', payload)
    return response.data
  },
}
