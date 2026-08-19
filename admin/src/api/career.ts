import { axiosInstance } from './client'
import { CareerEntity, GitHubRepo, WeeklySearchMetrics } from '@/types/career'

/**
 * Generic client for the career-domain (v2) CRUD REST API.
 *
 * Mirrors the backend's generic router factory
 * (api/src/routes/career_common.py): every resource exposes the same
 * `GET list / GET by id / POST / PUT / DELETE` shape at
 * `/career/{resource}`, always scoped server-side to the authenticated
 * user (never pass `user_id` in the payload).
 */
export interface ListParams {
  skip?: number
  limit?: number
}

const basePath = (resource: string) => `/career/${resource}`

export const careerApi = {
  list: async <T = CareerEntity>(resource: string, params: ListParams = {}): Promise<T[]> => {
    const { skip = 0, limit = 20 } = params
    const response = await axiosInstance.get<T[]>(basePath(resource), {
      params: { skip, limit },
    })
    return response.data
  },

  get: async <T = CareerEntity>(resource: string, id: number): Promise<T> => {
    const response = await axiosInstance.get<T>(`${basePath(resource)}/${id}`)
    return response.data
  },

  create: async <T = CareerEntity>(resource: string, payload: Record<string, unknown>): Promise<T> => {
    const response = await axiosInstance.post<T>(basePath(resource), payload)
    return response.data
  },

  update: async <T = CareerEntity>(
    resource: string,
    id: number,
    payload: Record<string, unknown>
  ): Promise<T> => {
    const response = await axiosInstance.put<T>(`${basePath(resource)}/${id}`, payload)
    return response.data
  },

  remove: async (resource: string, id: number): Promise<void> => {
    await axiosInstance.delete(`${basePath(resource)}/${id}`)
  },

  weeklyMetrics: async (limit = 12): Promise<WeeklySearchMetrics[]> => {
    const response = await axiosInstance.get<WeeklySearchMetrics[]>('/career/metrics/weekly', {
      params: { limit },
    })
    return response.data
  },

  githubRepos: async (): Promise<GitHubRepo[]> => {
    const response = await axiosInstance.get<GitHubRepo[]>('/career/github-profile/repos')
    return response.data
  },
}
