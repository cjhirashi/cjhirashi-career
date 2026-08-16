import axios, { AxiosInstance, AxiosError } from 'axios'
import { useAuthStore } from '@/stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://api:8001/api/v1'

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
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && originalRequest) {
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
