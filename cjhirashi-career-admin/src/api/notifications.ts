import { axiosInstance } from './client'

export interface UserNotification {
  id: string
  user_id: string
  kind: string
  title: string
  body: string | null
  resource_key: string | null
  resource_id: string | null
  read_at: string | null
  created_at: string
}

export const notificationsApi = {
  list: async (unread?: boolean): Promise<UserNotification[]> => {
    const response = await axiosInstance.get<UserNotification[]>('/notifications', {
      params: unread ? { unread: true } : undefined,
    })
    return response.data
  },

  unreadCount: async (): Promise<number> => {
    const response = await axiosInstance.get<{ count: number }>('/notifications/unread-count')
    return response.data.count
  },

  markRead: async (id: string): Promise<UserNotification> => {
    const response = await axiosInstance.post<UserNotification>(`/notifications/${id}/read`)
    return response.data
  },

  markAllRead: async (): Promise<void> => {
    await axiosInstance.post('/notifications/read-all')
  },
}
