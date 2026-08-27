import axios, { AxiosInstance, AxiosError } from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { reportClientError } from '@/utils/reportClientError'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor: add auth token
    this.client.interceptors.request.use(
      (config) => {
        const authState = useAuthStore.getState()
        if (authState.accessToken) {
          config.headers.Authorization = `Bearer ${authState.accessToken}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor: handle token refresh
    this.client.interceptors.response.use(
      (response) => {
        // A 2xx response whose body isn't JSON means something upstream of
        // the API (a proxy, a routing gap, a fallback to the SPA's own
        // index.html) intercepted the request instead of api_rest actually
        // answering it. Passing that through as if it were real data used
        // to reach a `.map()`/`.find()` somewhere downstream with a string
        // (e.g. HTML markup) instead of an array/object and crash the whole
        // page with no visible error - surfacing it as a rejected request
        // here instead lets every caller's existing isError/onError path
        // handle it like any other failed request. Exempt requests made
        // with `responseType: 'blob'` (file downloads, generated PDFs) -
        // those legitimately answer with a non-JSON content-type on
        // success (e.g. `application/pdf`, `image/png`).
        const contentType = response.headers?.['content-type']
        if (
          response.config?.responseType !== 'blob' &&
          typeof contentType === 'string' &&
          !contentType.includes('application/json')
        ) {
          return Promise.reject(
            Object.assign(new Error('Respuesta inesperada del servidor (no es JSON)'), {
              isAxiosError: true,
              config: response.config,
              response,
            })
          )
        }
        return response
      },
      async (error: AxiosError) => {
        const originalRequest = error.config
        const isAuthEndpoint =
          originalRequest?.url?.includes('/auth/login') ||
          originalRequest?.url?.includes('/auth/register')

        if (error.response?.status === 401 && originalRequest && !isAuthEndpoint) {
          const authState = useAuthStore.getState()

          if (authState.refreshToken) {
            try {
              const response = await this.refreshToken(authState.refreshToken)
              const { access_token: newAccessToken, expires_in: expiresIn } = response.data

              useAuthStore.setState({
                accessToken: newAccessToken,
                tokenExpiresAt: new Date(Date.now() + expiresIn * 1000),
              })

              // Retry original request with new token
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
              }
              return this.client(originalRequest)
            } catch (refreshError) {
              useAuthStore.setState({ accessToken: null, user: null })
              window.location.href = '/login'
              return Promise.reject(refreshError)
            }
          } else {
            useAuthStore.setState({ accessToken: null, user: null })
            window.location.href = '/login'
          }
        }

        // Registro central de fallas (ADR-018): errores de servidor y de red.
        const url = `${originalRequest?.baseURL ?? ''}${originalRequest?.url ?? ''}`
        const statusCode = error.response?.status
        if (!isAuthEndpoint && (statusCode === undefined || statusCode >= 500)) {
          reportClientError({
            message:
              (error.response?.data as { detail?: string })?.detail ||
              error.message ||
              'Error de red',
            source: `admin:api ${originalRequest?.method?.toUpperCase() ?? 'GET'} ${originalRequest?.url ?? '?'}`,
            error_type: statusCode ? `HTTP${statusCode}` : 'NetworkError',
            severity: statusCode && statusCode >= 500 ? 'error' : 'warning',
            context: { url, status_code: statusCode },
          })
        }

        return Promise.reject(error)
      }
    )
  }

  private refreshToken(refreshToken: string): Promise<any> {
    return this.client.post('/auth/refresh', { refresh_token: refreshToken })
  }

  public getClient(): AxiosInstance {
    return this.client
  }
}

export const apiClient = new ApiClient()
export const axiosInstance = apiClient.getClient()
