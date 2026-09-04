import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '@/stores/authStore'
import { mockUser, mockUser2 } from '../fixtures/mockData'

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      tokenExpiresAt: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    })
  })

  describe('initial state', () => {
    it('should initialize with correct default state', () => {
      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.accessToken).toBeNull()
      expect(state.refreshToken).toBeNull()
      expect(state.tokenExpiresAt).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
      expect(state.error).toBeNull()
    })
  })

  describe('setUser', () => {
    it('should set user and mark as authenticated', () => {
      const { setUser } = useAuthStore.getState()
      setUser(mockUser)

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.isAuthenticated).toBe(true)
    })

    it('should clear user and mark as not authenticated when passed null', () => {
      useAuthStore.setState({ user: mockUser, isAuthenticated: true })

      const { setUser } = useAuthStore.getState()
      setUser(null)

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('setTokens', () => {
    it('should set access token, refresh token, and expiration time', () => {
      const { setTokens } = useAuthStore.getState()
      const expiresIn = 3600

      setTokens('access_token_123', 'refresh_token_456', expiresIn)

      const state = useAuthStore.getState()
      expect(state.accessToken).toBe('access_token_123')
      expect(state.refreshToken).toBe('refresh_token_456')
      expect(state.tokenExpiresAt).toBeInstanceOf(Date)
      // Check expiration is approximately now + expiresIn
      const expectedExpiry = Date.now() + expiresIn * 1000
      expect(state.tokenExpiresAt!.getTime()).toBeCloseTo(expectedExpiry, -3)
    })
  })

  describe('setAccessToken', () => {
    it('should update access token and expiration time', () => {
      useAuthStore.setState({
        accessToken: 'old_token',
        tokenExpiresAt: new Date(),
      })

      const { setAccessToken } = useAuthStore.getState()
      const expiresIn = 7200

      setAccessToken('new_token_789', expiresIn)

      const state = useAuthStore.getState()
      expect(state.accessToken).toBe('new_token_789')
      const expectedExpiry = Date.now() + expiresIn * 1000
      expect(state.tokenExpiresAt!.getTime()).toBeCloseTo(expectedExpiry, -3)
    })
  })

  describe('setError', () => {
    it('should set error message', () => {
      const { setError } = useAuthStore.getState()
      const errorMessage = 'Invalid credentials'

      setError(errorMessage)

      const state = useAuthStore.getState()
      expect(state.error).toBe(errorMessage)
    })

    it('should set error to null', () => {
      useAuthStore.setState({ error: 'Some error' })

      const { setError } = useAuthStore.getState()
      setError(null)

      const state = useAuthStore.getState()
      expect(state.error).toBeNull()
    })
  })

  describe('setLoading', () => {
    it('should set loading state to true', () => {
      const { setLoading } = useAuthStore.getState()
      setLoading(true)

      const state = useAuthStore.getState()
      expect(state.isLoading).toBe(true)
    })

    it('should set loading state to false', () => {
      useAuthStore.setState({ isLoading: true })

      const { setLoading } = useAuthStore.getState()
      setLoading(false)

      const state = useAuthStore.getState()
      expect(state.isLoading).toBe(false)
    })
  })

  describe('logout', () => {
    it('should clear all authentication state', () => {
      useAuthStore.setState({
        user: mockUser,
        accessToken: 'token_123',
        refreshToken: 'refresh_123',
        tokenExpiresAt: new Date(Date.now() + 3600000),
        isAuthenticated: true,
        error: 'Some error',
      })

      const { logout } = useAuthStore.getState()
      logout()

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.accessToken).toBeNull()
      expect(state.refreshToken).toBeNull()
      expect(state.tokenExpiresAt).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(state.error).toBeNull()
    })
  })

  describe('clearError', () => {
    it('should clear error message', () => {
      useAuthStore.setState({ error: 'Some error' })

      const { clearError } = useAuthStore.getState()
      clearError()

      const state = useAuthStore.getState()
      expect(state.error).toBeNull()
    })

    it('should not affect other state when clearing error', () => {
      useAuthStore.setState({
        user: mockUser,
        isAuthenticated: true,
        error: 'Some error',
      })

      const { clearError } = useAuthStore.getState()
      clearError()

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.isAuthenticated).toBe(true)
      expect(state.error).toBeNull()
    })
  })

  describe('isTokenExpired', () => {
    it('should return true when tokenExpiresAt is null', () => {
      const { isTokenExpired } = useAuthStore.getState()
      expect(isTokenExpired()).toBe(true)
    })

    it('should return true when token is expired', () => {
      const expiredDate = new Date(Date.now() - 1000)
      useAuthStore.setState({ tokenExpiresAt: expiredDate })

      const { isTokenExpired } = useAuthStore.getState()
      expect(isTokenExpired()).toBe(true)
    })

    it('should return false when token is not expired', () => {
      const futureDate = new Date(Date.now() + 3600000)
      useAuthStore.setState({ tokenExpiresAt: futureDate })

      const { isTokenExpired } = useAuthStore.getState()
      expect(isTokenExpired()).toBe(false)
    })
  })

  describe('shouldRefreshToken', () => {
    it('should return false when tokenExpiresAt is null', () => {
      const { shouldRefreshToken } = useAuthStore.getState()
      expect(shouldRefreshToken()).toBe(false)
    })

    it('should return false when token is not close to expiration', () => {
      const futureDate = new Date(Date.now() + 3600000) // 1 hour away
      useAuthStore.setState({ tokenExpiresAt: futureDate })

      const { shouldRefreshToken } = useAuthStore.getState()
      expect(shouldRefreshToken()).toBe(false)
    })

    it('should return true when token is within 15 minutes of expiration', () => {
      const almostExpiredDate = new Date(Date.now() + 5 * 60 * 1000) // 5 minutes away
      useAuthStore.setState({ tokenExpiresAt: almostExpiredDate })

      const { shouldRefreshToken } = useAuthStore.getState()
      expect(shouldRefreshToken()).toBe(true)
    })

    it('should return false when token is already expired', () => {
      const expiredDate = new Date(Date.now() - 1000)
      useAuthStore.setState({ tokenExpiresAt: expiredDate })

      const { shouldRefreshToken } = useAuthStore.getState()
      expect(shouldRefreshToken()).toBe(false)
    })
  })

  describe('state updates', () => {
    it('should handle multiple state changes in sequence', () => {
      const { setUser, setTokens, setError, clearError } = useAuthStore.getState()

      setUser(mockUser)
      expect(useAuthStore.getState().isAuthenticated).toBe(true)

      setTokens('token_123', 'refresh_123', 3600)
      expect(useAuthStore.getState().accessToken).toBe('token_123')

      setError('Test error')
      expect(useAuthStore.getState().error).toBe('Test error')

      clearError()
      expect(useAuthStore.getState().error).toBeNull()
    })

    it('should allow switching between users', () => {
      const { setUser } = useAuthStore.getState()

      setUser(mockUser)
      expect(useAuthStore.getState().user?.id).toBe(mockUser.id)

      setUser(mockUser2)
      expect(useAuthStore.getState().user?.id).toBe(mockUser2.id)
      expect(useAuthStore.getState().user?.username).toBe(mockUser2.username)
    })
  })
})
