import { apiClient } from './client'
import { BlogPost } from '@/types'

export const blogApi = {
  getPosts: async (): Promise<BlogPost[]> => {
    const response = await apiClient.get<BlogPost[]>('/networking?type=blog')
    return response.data
  },

  getPostBySlug: async (slug: string): Promise<BlogPost> => {
    const response = await apiClient.get<BlogPost>(`/networking/${slug}`)
    return response.data
  },

  getLatestPosts: async (limit: number = 5): Promise<BlogPost[]> => {
    const response = await apiClient.get<BlogPost[]>(`/networking?type=blog&limit=${limit}`)
    return response.data
  },
}
