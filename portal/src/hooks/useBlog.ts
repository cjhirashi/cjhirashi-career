import { useQuery } from '@tanstack/react-query'
import { blogApi } from '@/api/blog'
import { BlogPost } from '@/types'

export const useBlogPosts = () => {
  return useQuery<BlogPost[]>({
    queryKey: ['blog-posts'],
    queryFn: () => blogApi.getPosts(),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  })
}

export const useLatestPosts = (limit: number = 5) => {
  return useQuery<BlogPost[]>({
    queryKey: ['latest-posts', limit],
    queryFn: () => blogApi.getLatestPosts(limit),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  })
}

export const useBlogPostBySlug = (slug: string) => {
  return useQuery<BlogPost>({
    queryKey: ['blog-post', slug],
    queryFn: () => blogApi.getPostBySlug(slug),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
    enabled: !!slug,
  })
}
