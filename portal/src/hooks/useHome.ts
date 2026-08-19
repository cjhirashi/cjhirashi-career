import { useQuery } from '@tanstack/react-query'
import { homeApi } from '@/api/home'
import { HomeContent } from '@/types'

export const useHome = () => {
  return useQuery<HomeContent>({
    queryKey: ['home'],
    queryFn: () => homeApi.getHome(),
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}
