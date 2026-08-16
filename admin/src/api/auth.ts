import { axiosInstance } from './client'
import { LoginResponse, TokenRefreshResponse, User } from '@/types'

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await axiosInstance.post<LoginResponse>('/auth/login', {
      username,
      password,
    })
    return response.data
  },

  register: async (
    username: string,
    email: string,
    password: string,
    fullName: string,
    phone?: string,
    country?: string,
    professionalTitle?: string
  ): Promise<User> => {
    const response = await axiosInstance.post<User>('/auth/register', {
      username,
      email,
      password,
      full_name: fullName,
      phone,
      country,
      professional_title: professionalTitle,
    })
    return response.data
  },

  refreshToken: async (refreshToken: string): Promise<TokenRefreshResponse> => {
    const response = await axiosInstance.post<TokenRefreshResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  logout: async (): Promise<void> => {
    await axiosInstance.post('/auth/logout')
  },

  changePassword: async (
    currentPassword: string,
    newPassword: string
  ): Promise<{ message: string }> => {
    const response = await axiosInstance.post<{ message: string }>(
      '/auth/change-password',
      {
        current_password: currentPassword,
        new_password: newPassword,
      }
    )
    return response.data
  },
}
