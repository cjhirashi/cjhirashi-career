import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { filesApi, UploadFileOptions } from '@/api/files'

const filesQueryKey = ['files'] as const

export function useFilesList(params: { skip?: number; limit?: number; category?: string } = {}) {
  return useQuery({
    queryKey: [...filesQueryKey, params],
    queryFn: () => filesApi.list(params),
  })
}

export function useFileCategories() {
  return useQuery({
    queryKey: [...filesQueryKey, 'categories'],
    queryFn: () => filesApi.categories(),
  })
}

export function useFileMutations() {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: filesQueryKey, exact: false })

  const uploadMutation = useMutation({
    mutationFn: ({ file, options }: { file: File; options?: UploadFileOptions }) =>
      filesApi.upload(file, options),
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => filesApi.remove(id),
    onSuccess: invalidate,
  })

  const visibilityMutation = useMutation({
    mutationFn: ({ id, isPublic }: { id: number; isPublic: boolean }) => filesApi.setVisibility(id, isPublic),
    onSuccess: invalidate,
  })

  return { uploadMutation, deleteMutation, visibilityMutation }
}
