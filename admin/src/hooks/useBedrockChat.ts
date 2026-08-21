import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { bedrockApi } from '@/api/bedrock'
import { agentTasksApi } from '@/api/agentTasks'
import { careerQueryKey } from '@/hooks/useCareerResource'
import { useBedrockChatStore } from '@/stores/bedrockChatStore'
import { getErrorMessage } from '@/utils/errors'
import { BedrockChatMessage } from '@/types/bedrock'

const conversationsKey = ['bedrock', 'conversations'] as const
const messagesKey = (sessionId: string) => ['bedrock', 'conversations', sessionId, 'messages'] as const

export function useBedrockConversations() {
  return useQuery({ queryKey: conversationsKey, queryFn: bedrockApi.listConversations })
}

export function useBedrockConversationMessages(sessionId: string) {
  return useQuery({
    queryKey: messagesKey(sessionId),
    queryFn: () => bedrockApi.getConversationMessages(sessionId),
  })
}

/**
 * Chat state + actions. Conversations/messages are server-persisted (see
 * api/bedrock.ts) - this hook is what wires the ephemeral send/status/error
 * state in `bedrockChatStore` to that React Query data, plus the one bit of
 * cross-cutting invalidation (career tables the agent just wrote to).
 */
export function useBedrockChat() {
  const queryClient = useQueryClient()
  const activeSessionId = useBedrockChatStore((s) => s.activeSessionId)
  const isSending = useBedrockChatStore((s) => s.isSending)
  const statusMessage = useBedrockChatStore((s) => s.statusMessage)
  const error = useBedrockChatStore((s) => s.error)
  const newConversation = useBedrockChatStore((s) => s.newConversation)
  const switchConversation = useBedrockChatStore((s) => s.switchConversation)

  const { data: conversations = [] } = useBedrockConversations()
  const { data: messages = [] } = useBedrockConversationMessages(activeSessionId)

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || isSending) return

    // Optimistic: show the user's own bubble immediately rather than
    // waiting for the whole turn (which can take minutes, see
    // bedrock.ts's CHAT_TIMEOUT_MS) - replaced by the real, DB-backed list
    // once the turn finishes and messagesKey is invalidated below.
    const optimisticMessage: BedrockChatMessage = {
      id: -Date.now(),
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    }
    queryClient.setQueryData<BedrockChatMessage[]>(messagesKey(activeSessionId), (old = []) => [
      ...old,
      optimisticMessage,
    ])

    useBedrockChatStore.setState({ isSending: true, statusMessage: null, error: null })

    try {
      const { affected_resources } = await bedrockApi.chat(activeSessionId, trimmed, (message) => {
        useBedrockChatStore.setState({ statusMessage: message })
      })

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: messagesKey(activeSessionId) }),
        queryClient.invalidateQueries({ queryKey: conversationsKey }),
      ])
      affected_resources.forEach((resource) => {
        queryClient.invalidateQueries({ queryKey: careerQueryKey(resource), exact: false })
      })
      useBedrockChatStore.setState({ isSending: false, statusMessage: null })
    } catch (err) {
      useBedrockChatStore.setState({ isSending: false, statusMessage: null, error: getErrorMessage(err) })
    }
  }

  const renameMutation = useMutation({
    mutationFn: ({ sessionId, title }: { sessionId: string; title: string }) => bedrockApi.renameConversation(sessionId, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: conversationsKey }),
  })

  const deleteMutation = useMutation({
    mutationFn: (sessionId: string) => bedrockApi.deleteConversation(sessionId),
    onSuccess: (_data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: conversationsKey })
      queryClient.removeQueries({ queryKey: messagesKey(sessionId) })
      if (sessionId === activeSessionId) newConversation()
    },
  })

  return {
    sessionId: activeSessionId,
    messages,
    conversations,
    isSending,
    statusMessage,
    error,
    send,
    newConversation,
    switchConversation,
    renameConversation: (sessionId: string, title: string) => renameMutation.mutate({ sessionId, title }),
    deleteConversation: (sessionId: string) => deleteMutation.mutate(sessionId),
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

export function useBedrockInstructions() {
  return useQuery({
    queryKey: ['bedrock', 'instructions'],
    queryFn: bedrockApi.getInstructions,
  })
}

export function useBedrockInstructionsUpdate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: bedrockApi.updateInstructions,
    onSuccess: (data) => {
      queryClient.setQueryData(['bedrock', 'instructions'], data)
    },
  })
}

export function useBedrockTools() {
  return useQuery({
    queryKey: ['bedrock', 'tools'],
    queryFn: bedrockApi.listTools,
  })
}

export function useBedrockToolMutations() {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['bedrock', 'tools'] })

  const createMutation = useMutation({
    mutationFn: bedrockApi.createTool,
    onSuccess: invalidate,
  })
  const setEnabledMutation = useMutation({
    mutationFn: ({ id, isEnabled }: { id: number; isEnabled: boolean }) => bedrockApi.setToolEnabled(id, isEnabled),
    onSuccess: invalidate,
  })
  const deleteMutation = useMutation({
    mutationFn: bedrockApi.deleteTool,
    onSuccess: invalidate,
  })

  return { createMutation, setEnabledMutation, deleteMutation }
}

export function useBedrockMemoryEvents(sessionId: string | null) {
  return useQuery({
    queryKey: ['bedrock', 'memory', 'events', sessionId],
    queryFn: () => bedrockApi.getMemoryEvents(sessionId as string),
    enabled: !!sessionId,
  })
}

export function useBedrockMemoryRecords(query: string) {
  return useQuery({
    queryKey: ['bedrock', 'memory', 'records', query],
    queryFn: () => bedrockApi.getMemoryRecords(query),
    enabled: query.trim().length > 0,
  })
}

export function useBedrockManualMemory() {
  return useMutation({ mutationFn: bedrockApi.addManualMemory })
}

export function useBedrockAuditLog(limit = 50) {
  return useQuery({
    queryKey: ['bedrock', 'audit-log', limit],
    queryFn: () => bedrockApi.getAuditLog(limit),
  })
}

export function useBedrockAuditRestore() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: bedrockApi.restoreAuditEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bedrock', 'audit-log'] })
    },
  })
}

export function useAgentTasks() {
  return useQuery({ queryKey: ['agent-tasks'], queryFn: agentTasksApi.list })
}

export function useAgentTaskMutations() {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['agent-tasks'] })

  const createMutation = useMutation({ mutationFn: agentTasksApi.create, onSuccess: invalidate })
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Parameters<typeof agentTasksApi.update>[1] }) =>
      agentTasksApi.update(id, payload),
    onSuccess: invalidate,
  })
  const deleteMutation = useMutation({ mutationFn: agentTasksApi.remove, onSuccess: invalidate })

  return { createMutation, updateMutation, deleteMutation }
}
