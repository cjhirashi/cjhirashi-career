import { axiosInstance } from './client'
import { CareerEntity, GitHubRepo, SearchOverview, WeeklySearchMetrics } from '@/types/career'

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
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  search?: string
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
    const { skip = 0, limit = 20, sortBy, sortDir, search } = params
    const response = await axiosInstance.get<T[]>(basePath(resource), {
      params: {
        skip,
        limit,
        sort_by: sortBy || undefined,
        sort_dir: sortDir || undefined,
        search: search || undefined,
      },
    })
    return response.data
  },

  count: async (resource: string): Promise<number> => {
    const response = await axiosInstance.get<{ count: number }>(`${basePath(resource)}/count`)
    return response.data.count
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

  searchOverview: async (): Promise<SearchOverview> => {
    const response = await axiosInstance.get<SearchOverview>('/career/metrics/search-overview')
    return response.data
  },

  /** Renders a CV version's `content` (Markdown) into a PDF via the PDF
   * Generator, proxied through the API - `cv-versions`-only, so it lives
   * here as a one-off instead of a generic `careerApi` verb. Raw bytes,
   * authenticated the normal way (JWT header via axiosInstance), same
   * blob-download shape as `filesApi.downloadBlob`. */
  generateResourcePdf: async (
    resourceKey: string,
    id: number
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
