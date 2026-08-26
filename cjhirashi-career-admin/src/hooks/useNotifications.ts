import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/api/notifications'

export function useNotifications() {
  const listQuery = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list(),
    refetchInterval: 20_000,
  })
  const unreadQuery = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: notificationsApi.unreadCount,
    refetchInterval: 20_000,
  })
  return { listQuery, unreadCount: unreadQuery.data ?? 0 }
}

export function useNotificationMutations() {
  const queryClient = useQueryClient()
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
    queryClient.invalidateQueries({ queryKey: ['agent-tasks'] })
  }
  const markRead = useMutation({ mutationFn: notificationsApi.markRead, onSuccess: invalidate })
  const markAllRead = useMutation({ mutationFn: notificationsApi.markAllRead, onSuccess: invalidate })
  return { markRead, markAllRead }
}
