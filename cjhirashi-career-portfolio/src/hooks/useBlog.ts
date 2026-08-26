import { useQuery } from '@tanstack/react-query'
import { blogApi } from '@/api/blog'
import { BlogPost } from '@/types'

export const useBlogPosts = () => {
  return useQuery<BlogPost[]>({
    queryKey: ['blog-posts'],
    queryFn: () => blogApi.getPosts(),
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}

export const useBlogPostBySlug = (slug: string) => {
  return useQuery<BlogPost>({
    queryKey: ['blog-post', slug],
    queryFn: () => blogApi.getPostBySlug(slug),
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled: !!slug,
  })
}
