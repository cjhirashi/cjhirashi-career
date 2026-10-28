import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/api/projects'
import { Project } from '@/types'

export const useProjects = () => {
  return useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getProjects(),
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}

export const useProjectBySlug = (slug: string) => {
  return useQuery<Project>({
    queryKey: ['project', slug],
    queryFn: () => projectsApi.getProjectBySlug(slug),
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled: !!slug,
  })
}
