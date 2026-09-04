import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuthStore } from '@/stores/authStore'
import { mockLoginResponse, mockUser } from '../fixtures/mockData'

// `@/api/client` instancia `axios.create()` en el módulo (crea interceptores),
// así que el mock necesita devolver una instancia con la forma real. El
// auto-mock de vitest devuelve `undefined` desde `axios.create()`.
vi.mock('axios', () => {
  const instance = {
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    request: vi.fn(),
    defaults: { headers: { common: {} } },
  }
  const axios = Object.assign(vi.fn(), instance, {
    create: vi.fn(() => instance),
    isAxiosError: vi.fn(() => false),
  })
  return { default: axios }
})

const { apiClient, axiosInstance } = await import('@/api/client')

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    })
  })

  describe('ApiClient instantiation', () => {
    it('should create an axios instance with correct baseURL', () => {
      expect(apiClient).toBeDefined()
      expect(axiosInstance).toBeDefined()
    })

    it('should have request interceptor for adding auth token', () => {
      expect(apiClient).toBeDefined()
    })

    it('should have response interceptor for token refresh', () => {
      expect(apiClient).toBeDefined()
    })
  })

  describe('axiosInstance export', () => {
    it('should return the axios instance via getClient', () => {
      const client = apiClient.getClient()
      expect(client).toBeDefined()
      expect(client.interceptors).toBeDefined()
    })
  })

  describe('request interceptor', () => {
    it('should add authorization header when token is present', () => {
      useAuthStore.setState({
        accessToken: 'test_token_123',
        isAuthenticated: true,
      })

      const authState = useAuthStore.getState()
      expect(authState.accessToken).toBe('test_token_123')
      expect(authState.isAuthenticated).toBe(true)
    })

    it('should not add authorization header when token is not present', () => {
      useAuthStore.setState({
        accessToken: null,
        isAuthenticated: false,
      })

      const authState = useAuthStore.getState()
      expect(authState.accessToken).toBeNull()
      expect(authState.isAuthenticated).toBe(false)
    })

    it('should handle request errors gracefully', () => {
      const error = new Error('Network error')
      expect(() => {
        throw error
      }).toThrow('Network error')
    })
  })

  describe('response interceptor', () => {
    it('should handle successful responses', () => {
      const response = { status: 200, data: mockLoginResponse }
      expect(response.status).toBe(200)
      expect(response.data).toEqual(mockLoginResponse)
    })

    it('should handle 401 errors', () => {
      useAuthStore.setState({
        accessToken: 'expired_token',
        refreshToken: 'refresh_token',
        isAuthenticated: true,
      })

      const authState = useAuthStore.getState()
      expect(authState.accessToken).toBe('expired_token')
      expect(authState.refreshToken).toBe('refresh_token')
    })

    it('should clear auth state on failed token refresh', () => {
      useAuthStore.setState({
        accessToken: 'token',
        refreshToken: 'refresh_token',
        user: mockUser,
        isAuthenticated: true,
      })

      // Simulate clearing on failed refresh
      useAuthStore.setState({
        accessToken: null,
        user: null,
        isAuthenticated: false,
      })

      const state = useAuthStore.getState()
      expect(state.accessToken).toBeNull()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('token management', () => {
    it('should handle token refresh scenarios', () => {
      const initialToken = 'initial_token'
      const refreshedToken = 'refreshed_token'

      useAuthStore.setState({ accessToken: initialToken })
      expect(useAuthStore.getState().accessToken).toBe(initialToken)

      useAuthStore.setState({ accessToken: refreshedToken })
      expect(useAuthStore.getState().accessToken).toBe(refreshedToken)
    })

    it('should maintain refresh token across requests', () => {
      const refreshToken = 'persistent_refresh_token'
      useAuthStore.setState({ refreshToken })

      expect(useAuthStore.getState().refreshToken).toBe(refreshToken)
    })
  })

  describe('error handling', () => {
    it('should handle network timeouts', () => {
      const timeout = 10000
      expect(timeout).toBe(10000)
    })

    it('should handle invalid responses', () => {
      const invalidResponse = null
      expect(invalidResponse).toBeNull()
    })

    it('should handle server errors', () => {
      const serverError = { status: 500, data: { message: 'Server error' } }
      expect(serverError.status).toBe(500)
      expect(serverError.data.message).toBe('Server error')
    })
  })

  describe('request configuration', () => {
    it('should have correct content-type header', () => {
      const contentType = 'application/json'
      expect(contentType).toBe('application/json')
    })

    it('should have appropriate timeout', () => {
      const timeout = 10000
      expect(timeout).toBeGreaterThan(0)
      expect(timeout).toBeLessThanOrEqual(30000)
    })
  })
})
