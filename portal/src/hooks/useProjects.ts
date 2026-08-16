import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/api/projects'
import { Project } from '@/types'

export const useProjects = () => {
  return useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getProjects(),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  })
}

export const useFeaturedProjects = (limit: number = 3) => {
  return useQuery<Project[]>({
    queryKey: ['featured-projects', limit],
    queryFn: () => projectsApi.getFeaturedProjects(limit),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  })
}

export const useProjectById = (id: string) => {
  return useQuery<Project>({
    queryKey: ['project', id],
    queryFn: () => projectsApi.getProjectById(id),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
    enabled: !!id,
  })
}
