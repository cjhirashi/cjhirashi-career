import axios, { AxiosInstance } from 'axios'

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

  put<T>(url: string, data?: unknown) {
    return this.instance.put<T>(url, data)
  }

  delete<T>(url: string) {
    return this.instance.delete<T>(url)
  }
}

export const apiClient = new ApiClient()
