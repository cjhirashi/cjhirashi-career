import { axiosInstance } from './client'
import { LinkedInPostEntity, LinkedInStatus } from '@/types/linkedin'

/**
 * Client for the LinkedIn integration (`/linkedin`). Mirrors
 * `api/src/routes/linkedin.py` - status/connect/disconnect + publishing.
 */
export const linkedinApi = {
  status: async (): Promise<LinkedInStatus> => {
    const response = await axiosInstance.get<LinkedInStatus>('/linkedin/status')
    return response.data
  },

  /** Returns LinkedIn's own authorize URL - the caller navigates the browser there. */
  connect: async (): Promise<string> => {
    const response = await axiosInstance.get<{ authorize_url: string }>('/linkedin/connect')
    return response.data.authorize_url
  },

  disconnect: async (): Promise<void> => {
    await axiosInstance.delete('/linkedin/disconnect')
  },

  listPosts: async (): Promise<LinkedInPostEntity[]> => {
    const response = await axiosInstance.get<LinkedInPostEntity[]>('/linkedin/posts')
    return response.data
  },

  createPost: async (params: { text: string; image?: File; scheduledAt?: string }): Promise<LinkedInPostEntity> => {
    const formData = new FormData()
    formData.append('text', params.text)
    if (params.image) formData.append('image', params.image)
    if (params.scheduledAt) formData.append('scheduled_at', params.scheduledAt)

    const response = await axiosInstance.post<LinkedInPostEntity>('/linkedin/posts', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  cancelPost: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/linkedin/posts/${id}`)
  },
}
