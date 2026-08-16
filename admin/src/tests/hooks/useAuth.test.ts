import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/authStore'
import * as authApi from '@/api/auth'

vi.mock('@/api/auth')

describe('useAuth', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    })
    vi.clearAllMocks()
  })

  it('should initialize with no user', () => {
    const { result } = renderHook(() => useAuth())
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('should handle login successfully', async () => {
    const mockResponse = {
      access_token: 'token123',
      refresh_token: 'refresh123',
      expires_in: 3600,
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        full_name: 'Test User',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    }

    vi.spyOn(authApi, 'login').mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useAuth())

    await act(async () => {
      await result.current.login('testuser', 'password123')
    })

    expect(result.current.user).toEqual(mockResponse.user)
    expect(result.current.isAuthenticated).toBe(true)
  })

  it('should clear error on clearError', () => {
    useAuthStore.setState({ error: 'Some error' })

    const { result } = renderHook(() => useAuth())
    expect(result.current.error).toBe('Some error')

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBeNull()
  })

  it('should check token expiration', () => {
    const { result } = renderHook(() => useAuth())

    expect(result.current.isTokenExpired()).toBe(true)

    useAuthStore.setState({
      tokenExpiresAt: new Date(Date.now() + 3600000),
    })

    expect(result.current.isTokenExpired()).toBe(false)
  })
})
