import axios, { AxiosInstance } from 'axios'
import { reportClientError } from '@/utils/reportClientError'

const getApiUrl = (): string => {
  // In development, use proxy to /api which is rewritten to http://api:8001/api/v1
  // In production, use the environment variable
  if (import.meta.env.DEV) {
    return '/api'
  }
  return import.meta.env.VITE_API_URL || '/api'
}

class ApiClient {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: getApiUrl(),
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add response interceptor for error handling
    this.instance.interceptors.response.use(
      response => response,
      error => {
        console.error('API Error:', error.response?.data || error.message)
        const status = error.response?.status
        if (status === undefined || status >= 500) {
          reportClientError({
            message:
              error.response?.data?.detail || error.message || 'Error de red',
            source: `portfolio:api ${error.config?.method?.toUpperCase() ?? 'GET'} ${error.config?.url ?? '?'}`,
            error_type: status ? `HTTP${status}` : 'NetworkError',
            severity: status && status >= 500 ? 'error' : 'warning',
            context: { status_code: status },
          })
        }
        return Promise.reject(error)
      }
    )
  }

  get<T>(url: string) {
    return this.instance.get<T>(url)
  }

  post<T>(url: string, data?: unknown) {
    return this.instance.post<T>(url, data)
  }

  /** Fire-and-forget POST that survives page unload/tab close, unlike a
   * normal fetch/XHR which the browser can abort mid-flight. Used only for
   * tracking calls sent from a `pagehide`/`visibilitychange` handler. Returns
   * false (caller should ignore) if the browser couldn't queue it. */
  postBeacon(url: string, data: unknown): boolean {
    if (typeof navigator === 'undefined' || !navigator.sendBeacon) return false
    const blob = new Blob([JSON.stringify(data)], { type: 'application/json' })
    return navigator.sendBeacon(`${this.instance.defaults.baseURL}${url}`, blob)
  }

  put<T>(url: string, data?: unknown) {
    return this.instance.put<T>(url, data)
  }

  delete<T>(url: string) {
    return this.instance.delete<T>(url)
  }
}

export const apiClient = new ApiClient()
