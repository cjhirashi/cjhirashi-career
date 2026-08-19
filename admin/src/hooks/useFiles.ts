import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { filesApi } from '@/api/files'

const filesQueryKey = ['files'] as const

export function useFilesList(params: { skip?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: [...filesQueryKey, params],
    queryFn: () => filesApi.list(params),
  })
}

export function useFileMutations() {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: filesQueryKey, exact: false })

  const uploadMutation = useMutation({
    mutationFn: ({ file, description }: { file: File; description?: string }) =>
      filesApi.upload(file, description),
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => filesApi.remove(id),
    onSuccess: invalidate,
  })

  return { uploadMutation, deleteMutation }
}
