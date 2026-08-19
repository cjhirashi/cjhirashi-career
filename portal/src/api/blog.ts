import { apiClient } from './client'
import { BlogPost } from '@/types'

export const blogApi = {
  getPosts: async (): Promise<BlogPost[]> => {
    const response = await apiClient.get<BlogPost[]>('/public/blog')
    return response.data
  },

  getPostBySlug: async (slug: string): Promise<BlogPost> => {
    const response = await apiClient.get<BlogPost>(`/public/blog/${slug}`)
    return response.data
  },
}
