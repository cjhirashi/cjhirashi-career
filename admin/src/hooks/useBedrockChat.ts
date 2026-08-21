import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { bedrockApi } from '@/api/bedrock'
import { careerQueryKey } from '@/hooks/useCareerResource'
import { useBedrockChatStore } from '@/stores/bedrockChatStore'

/**
 * Wraps `bedrockChatStore` with the one bit of React Query it needs to touch:
 * invalidating whichever career tables the agent just wrote to, so a table
 * left open in another tab/view refreshes itself instead of showing stale
 * data. Kept as a hook (not inside the store module) because query
 * invalidation needs `useQueryClient()`, a React hook.
 */
export function useBedrockChat() {
  const queryClient = useQueryClient()
  const store = useBedrockChatStore()

  const send = async (text: string) => {
    const affectedResources = await store.sendMessage(text)
    affectedResources.forEach((resource) => {
      queryClient.invalidateQueries({ queryKey: careerQueryKey(resource), exact: false })
    })
  }

  return {
    sessionId: store.sessionId,
    messages: store.messages,
    isSending: store.isSending,
    error: store.error,
    send,
    clearConversation: store.clearConversation,
  }
}

export function useBedrockModel() {
  return useQuery({
    queryKey: ['bedrock', 'model'],
    queryFn: bedrockApi.getModel,
    retry: false,
  })
}

export function useBedrockModelSwitch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: bedrockApi.switchModel,
    onSuccess: (data) => {
      queryClient.setQueryData(['bedrock', 'model'], data)
    },
  })
}

export function useBedrockUsageMetrics(days = 30) {
  return useQuery({
    queryKey: ['bedrock', 'usage-metrics', days],
    queryFn: () => bedrockApi.usageMetrics(days),
  })
}
