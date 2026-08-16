import { useQuery } from '@tanstack/react-query'
import { identityApi } from '@/api/identity'
import { Identity } from '@/types'

export const useIdentity = () => {
  return useQuery<Identity>({
    queryKey: ['identity'],
    queryFn: () => identityApi.getIdentity(),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  })
}

export const useCompetencies = () => {
  return useQuery<string[]>({
    queryKey: ['competencies'],
    queryFn: () => identityApi.getCompetencies(),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  })
}
