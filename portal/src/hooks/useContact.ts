import { useQuery } from '@tanstack/react-query'
import { contactApi } from '@/api/contact'
import { ContactContent } from '@/types'

export const useContact = () => {
  return useQuery<ContactContent>({
    queryKey: ['contact'],
    queryFn: () => contactApi.getContact(),
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}
