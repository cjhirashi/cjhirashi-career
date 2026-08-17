import { useCallback, useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/auth'

export const useAuth = () => {
  const {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isLoading,
    error,
    setUser,
    setTokens,
    setAccessToken,
    setError,
    setLoading,
    logout: logoutState,
    clearError,
    shouldRefreshToken,
    isTokenExpired,
  } = useAuthStore()

  // Token refresh effect
  useEffect(() => {
    if (!shouldRefreshToken() || !refreshToken) return

    const timer = setTimeout(() => {
      handleRefreshToken()
    }, 1000)

    return () => clearTimeout(timer)
  }, [refreshToken, shouldRefreshToken])

  // Check token expiration on mount
  useEffect(() => {
    if (isAuthenticated && isTokenExpired()) {
      logoutState()
    }
  }, [isAuthenticated, isTokenExpired, logoutState])

  const handleLogin = useCallback(
    async (username: string, password: string) => {
      setLoading(true)
      clearError()

      try {
        const response = await authApi.login(username, password)
        setUser(response.user)
        setTokens(response.access_token, response.refresh_token, response.expires_in)
        return response
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Login failed'
        setError(message)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [setLoading, clearError, setUser, setTokens, setError]
  )

  const handleRegister = useCallback(
    async (
      username: string,
      email: string,
      password: string,
      fullName: string,
      phone?: string,
      country?: string,
      professionalTitle?: string
    ) => {
      setLoading(true)
      clearError()

      try {
        const user = await authApi.register(
          username,
          email,
          password,
          fullName,
          phone,
          country,
          professionalTitle
        )
        return user
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Registration failed'
        setError(message)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [setLoading, clearError, setError]
  )

  const handleRefreshToken = useCallback(async () => {
    if (!refreshToken) return

    try {
      const response = await authApi.refreshToken(refreshToken)
      setAccessToken(response.access_token, response.expires_in)
    } catch (err: any) {
      console.error('Token refresh failed', err)
      logoutState()
    }
  }, [refreshToken, setAccessToken, logoutState])

  const handleLogout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch (err) {
      console.error('Logout API call failed', err)
    } finally {
      logoutState()
    }
  }, [logoutState])

  const handleChangePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      setLoading(true)
      clearError()

      try {
        await authApi.changePassword(currentPassword, newPassword)
        return { success: true }
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Password change failed'
        setError(message)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [setLoading, clearError, setError]
  )

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    refreshAccessToken: handleRefreshToken,
    changePassword: handleChangePassword,
    clearError,
    isTokenExpired,
    shouldRefreshToken,
  }
}
