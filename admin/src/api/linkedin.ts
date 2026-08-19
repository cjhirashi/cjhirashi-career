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

  createPost: async (text: string): Promise<LinkedInPostEntity> => {
    const response = await axiosInstance.post<LinkedInPostEntity>('/linkedin/posts', { text })
    return response.data
  },
}
