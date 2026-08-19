import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { linkedinApi } from '@/api/linkedin'

const linkedinStatusKey = ['linkedin', 'status'] as const
const linkedinPostsKey = ['linkedin', 'posts'] as const

export function useLinkedInStatus() {
  return useQuery({
    queryKey: linkedinStatusKey,
    queryFn: linkedinApi.status,
  })
}

export function useLinkedInPosts() {
  return useQuery({
    queryKey: linkedinPostsKey,
    queryFn: linkedinApi.listPosts,
  })
}

export function useLinkedInMutations() {
  const queryClient = useQueryClient()
  const invalidateStatus = () => queryClient.invalidateQueries({ queryKey: linkedinStatusKey })

  const disconnectMutation = useMutation({
    mutationFn: linkedinApi.disconnect,
    onSuccess: invalidateStatus,
  })

  const createPostMutation = useMutation({
    mutationFn: (text: string) => linkedinApi.createPost(text),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: linkedinPostsKey }),
  })

  return { disconnectMutation, createPostMutation }
}
