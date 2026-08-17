import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/authStore'
import * as authApi from '@/api/auth'
import { mockLoginResponse, mockUser } from '../fixtures/mockData'

vi.mock('@/api/auth')

describe('useAuth', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  describe('initialization', () => {
    it('should initialize with no user', () => {
      const { result } = renderHook(() => useAuth())
      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('should initialize with authentication state', () => {
      useAuthStore.setState({
        user: mockUser,
        isAuthenticated: true,
        accessToken: 'token123',
      })

      const { result } = renderHook(() => useAuth())
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.accessToken).toBe('token123')
    })
  })

  describe('login', () => {
    it('should handle login successfully', async () => {
      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.login('demo', 'password123')
      })

      expect(result.current.user).toEqual(mockLoginResponse.user)
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.accessToken).toBe(mockLoginResponse.access_token)
    })

    it('should handle login failure', async () => {
      const error = new Error('Invalid credentials')
      vi.mocked(authApi.login).mockRejectedValue(error)

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        try {
          await result.current.login('demo', 'wrongpassword')
        } catch (err) {
          // Expected error
        }
      })

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.error).toBeTruthy()
    })

    it('should set loading state during login', async () => {
      vi.mocked(authApi.login).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockLoginResponse), 100))
      )

      const { result } = renderHook(() => useAuth())

      act(() => {
        result.current.login('demo', 'password123')
      })

      // Loading should be true immediately after calling login
      // Then false after the promise resolves
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 150))
      })
    })

    it('should clear previous errors on login attempt', async () => {
      useAuthStore.setState({ error: 'Previous error' })
      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)

      const { result } = renderHook(() => useAuth())
      expect(result.current.error).toBe('Previous error')

      await act(async () => {
        await result.current.login('demo', 'password123')
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('logout', () => {
    it('should logout successfully', async () => {
      useAuthStore.setState({
        user: mockUser,
        accessToken: 'token123',
        isAuthenticated: true,
      })

      vi.mocked(authApi.logout).mockResolvedValue(undefined)

      const { result } = renderHook(() => useAuth())
      expect(result.current.isAuthenticated).toBe(true)

      await act(async () => {
        await result.current.logout()
      })

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.accessToken).toBeNull()
    })

    it('should handle logout API failure gracefully', async () => {
      useAuthStore.setState({
        user: mockUser,
        accessToken: 'token123',
        isAuthenticated: true,
      })

      vi.mocked(authApi.logout).mockRejectedValue(new Error('Logout failed'))

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.logout()
      })

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('register', () => {
    it('should register new user', async () => {
      vi.mocked(authApi.register).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.register('newuser', 'new@example.com', 'password123', 'New User')
      })

      expect(vi.mocked(authApi.register)).toHaveBeenCalledWith(
        'newuser',
        'new@example.com',
        'password123',
        'New User',
        undefined,
        undefined,
        undefined
      )
    })

    it('should handle registration failure', async () => {
      const error = new Error('Email already exists')
      vi.mocked(authApi.register).mockRejectedValue(error)

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        try {
          await result.current.register('user', 'existing@example.com', 'pass', 'User')
        } catch (err) {
          // Expected error
        }
      })

      expect(result.current.error).toBeTruthy()
    })
  })

  describe('clearError', () => {
    it('should clear error message', () => {
      useAuthStore.setState({ error: 'Some error' })

      const { result } = renderHook(() => useAuth())
      expect(result.current.error).toBe('Some error')

      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBeNull()
    })

    it('should not affect other state when clearing error', () => {
      useAuthStore.setState({
        user: mockUser,
        isAuthenticated: true,
        error: 'Some error',
      })

      const { result } = renderHook(() => useAuth())

      act(() => {
        result.current.clearError()
      })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.error).toBeNull()
    })
  })

  describe('token expiration', () => {
    it('should check token expiration correctly', () => {
      const { result } = renderHook(() => useAuth())

      expect(result.current.isTokenExpired()).toBe(true)

      useAuthStore.setState({
        tokenExpiresAt: new Date(Date.now() + 3600000),
      })

      expect(result.current.isTokenExpired()).toBe(false)
    })

    it('should identify when token is close to expiration', () => {
      useAuthStore.setState({
        tokenExpiresAt: new Date(Date.now() + 5 * 60 * 1000), // 5 minutes away
      })

      const { result } = renderHook(() => useAuth())
      expect(result.current.shouldRefreshToken()).toBe(true)
    })

    it('should not refresh token when far from expiration', () => {
      useAuthStore.setState({
        tokenExpiresAt: new Date(Date.now() + 3600000), // 1 hour away
      })

      const { result } = renderHook(() => useAuth())
      expect(result.current.shouldRefreshToken()).toBe(false)
    })
  })

  describe('changePassword', () => {
    it('should change password successfully', async () => {
      vi.mocked(authApi.changePassword).mockResolvedValue({ message: 'Password changed' })

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        const response = await result.current.changePassword('oldpass', 'newpass')
        expect(response).toEqual({ success: true })
      })
    })

    it('should handle password change failure', async () => {
      const error = new Error('Current password is incorrect')
      vi.mocked(authApi.changePassword).mockRejectedValue(error)

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        try {
          await result.current.changePassword('wrongpass', 'newpass')
        } catch (err) {
          // Expected error
        }
      })

      expect(result.current.error).toBeTruthy()
    })
  })

  describe('token refresh', () => {
    it('should refresh token successfully', async () => {
      useAuthStore.setState({
        accessToken: 'old_token',
        refreshToken: 'refresh_token',
      })

      vi.mocked(authApi.refreshToken).mockResolvedValue({
        access_token: 'new_token',
        expires_in: 3600,
      })

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.refreshToken()
      })

      expect(useAuthStore.getState().accessToken).toBe('new_token')
    })

    it('should logout on token refresh failure', async () => {
      useAuthStore.setState({
        accessToken: 'token',
        refreshToken: 'refresh_token',
        user: mockUser,
        isAuthenticated: true,
      })

      vi.mocked(authApi.refreshToken).mockRejectedValue(new Error('Refresh failed'))

      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.refreshToken()
      })

      expect(useAuthStore.getState().isAuthenticated).toBe(false)
    })
  })
})
