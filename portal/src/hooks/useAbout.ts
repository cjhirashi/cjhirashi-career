import { useQuery } from '@tanstack/react-query'
import { aboutApi } from '@/api/about'
import { AboutContent } from '@/types'

export const useAbout = () => {
  return useQuery<AboutContent>({
    queryKey: ['about'],
    queryFn: () => aboutApi.getAbout(),
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}
