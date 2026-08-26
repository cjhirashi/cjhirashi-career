import { axiosInstance } from './client'
import {
  CareerEntity,
  GitHubRepo,
  JobDiscoveryRunResponse,
  JobDiscoverySaveResponse,
  JobListing,
  JobProviderStatus,
  SearchOverview,
  WeeklySearchMetrics,
} from '@/types/career'

/**
 * Generic client for the career-domain (v2) CRUD REST API.
 *
 * Mirrors the backend's generic router factory
 * (api/src/routes/career_common.py): every resource exposes the same
 * `GET list / GET by id / POST / PUT / DELETE` shape at
 * `/career/{resource}`, always scoped server-side to the authenticated
 * user (never pass `user_id` in the payload).
 */
export type ListFilters = Record<string, string | string[] | boolean>

export interface ListParams {
  skip?: number
  limit?: number
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  search?: string
  filters?: ListFilters
}

const basePath = (resource: string) => `/career/${resource}`

/** Pulls a filename out of a `Content-Disposition: attachment; filename="..."`
 * header (also accepts the unquoted / `filename*=UTF-8''...` RFC 5987 forms).
 * Returns null if the header is missing or unparseable, so the caller can
 * fall back to a filename of its own. */
const filenameFromContentDisposition = (headerValue: unknown): string | null => {
  if (typeof headerValue !== 'string') return null
  const utf8Match = headerValue.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match) {
    try {
      return decodeURIComponent(utf8Match[1].trim())
    } catch {
      return utf8Match[1].trim()
    }
  }
  const plainMatch = headerValue.match(/filename="?([^";]+)"?/i)
  return plainMatch ? plainMatch[1].trim() : null
}

export const careerApi = {
  list: async <T = CareerEntity>(resource: string, params: ListParams = {}): Promise<T[]> => {
    const { skip = 0, limit = 20, sortBy, sortDir, search, filters } = params
    const response = await axiosInstance.get<T[]>(basePath(resource), {
      params: {
        skip,
        limit,
        sort_by: sortBy || undefined,
        sort_dir: sortDir || undefined,
        search: search || undefined,
        filters: filters && Object.keys(filters).length > 0 ? JSON.stringify(filters) : undefined,
      },
    })
    return response.data
  },

  count: async (resource: string, params: Pick<ListParams, 'search' | 'filters'> = {}): Promise<number> => {
    const { search, filters } = params
    const response = await axiosInstance.get<{ count: number }>(`${basePath(resource)}/count`, {
      params: {
        search: search || undefined,
        filters: filters && Object.keys(filters).length > 0 ? JSON.stringify(filters) : undefined,
      },
    })
    return response.data.count
  },

  get: async <T = CareerEntity>(resource: string, id: string): Promise<T> => {
    const response = await axiosInstance.get<T>(`${basePath(resource)}/${id}`)
    return response.data
  },

  create: async <T = CareerEntity>(resource: string, payload: Record<string, unknown>): Promise<T> => {
    const response = await axiosInstance.post<T>(basePath(resource), payload)
    return response.data
  },

  update: async <T = CareerEntity>(
    resource: string,
    id: string,
    payload: Record<string, unknown>
  ): Promise<T> => {
    const response = await axiosInstance.put<T>(`${basePath(resource)}/${id}`, payload)
    return response.data
  },

  remove: async (resource: string, id: string): Promise<void> => {
    await axiosInstance.delete(`${basePath(resource)}/${id}`)
  },

  /** Unique values already stored in a text column (creatable selects). */
  distinct: async (resource: string, field: string): Promise<string[]> => {
    const response = await axiosInstance.get<{ field: string; values: string[] }>(
      `${basePath(resource)}/distinct/${encodeURIComponent(field)}`
    )
    return response.data.values
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

  searchOverview: async (): Promise<SearchOverview> => {
    const response = await axiosInstance.get<SearchOverview>('/career/metrics/search-overview')
    return response.data
  },

  listJobProviders: async (): Promise<JobProviderStatus[]> => {
    const response = await axiosInstance.get<JobProviderStatus[]>('/career/job-discoveries/providers')
    return response.data
  },

  runJobDiscovery: async (payload: {
    query?: string
    location?: string
    providers?: string[]
    target_role_id?: string
    include_company_boards?: boolean
    remote?: boolean
  }): Promise<JobDiscoveryRunResponse> => {
    const response = await axiosInstance.post<JobDiscoveryRunResponse>('/career/job-discoveries/run', payload)
    return response.data
  },

  importJobUrl: async (url: string): Promise<JobListing> => {
    const response = await axiosInstance.post<JobListing>('/career/job-discoveries/import-url', { url })
    return response.data
  },

  saveJobListings: async (
    listings: JobListing[],
    targetRoleId?: string
  ): Promise<JobDiscoverySaveResponse> => {
    const response = await axiosInstance.post<JobDiscoverySaveResponse>('/career/job-discoveries/save', {
      listings,
      target_role_id: targetRoleId,
    })
    return response.data
  },

  /** Renders a CV version's `content` (Markdown) into a PDF via the PDF
   * Generator, proxied through the API - `cv-versions`-only, so it lives
   * here as a one-off instead of a generic `careerApi` verb. Raw bytes,
   * authenticated the normal way (JWT header via axiosInstance), same
   * blob-download shape as `filesApi.downloadBlob`. */
  generateResourcePdf: async (
    resourceKey: string,
    id: string
  ): Promise<{ blob: Blob; filename: string | null }> => {
    const response = await axiosInstance.post(`${basePath(resourceKey)}/${id}/pdf`, null, {
      responseType: 'blob',
    })
    return {
      blob: response.data,
      filename: filenameFromContentDisposition(response.headers?.['content-disposition']),
    }
  },
}
