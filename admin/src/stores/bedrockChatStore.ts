import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { bedrockApi } from '@/api/bedrock'
import { getErrorMessage } from '@/utils/errors'
import { BedrockChatMessage } from '@/types/bedrock'

/** AgentCore Harness requires `runtimeSessionId` to be at least 33
 * characters - `crypto.randomUUID()` (36 chars) comfortably clears that. */
const newSessionId = () => crypto.randomUUID()

interface BedrockChatState {
  sessionId: string
  messages: BedrockChatMessage[]
  isSending: boolean
  error: string | null

  // Returns the resource_keys the turn touched, so callers can invalidate
  // their React Query cache for those tables (see useBedrockChat.ts).
  sendMessage: (text: string) => Promise<string[]>
  clearConversation: () => void
}

export const useBedrockChatStore = create<BedrockChatState>()(
  persist(
    immer((set, get) => ({
      sessionId: newSessionId(),
      messages: [],
      isSending: false,
      error: null,

      sendMessage: async (text: string) => {
        const trimmed = text.trim()
        if (!trimmed || get().isSending) return []

        const userMessage: BedrockChatMessage = {
          id: crypto.randomUUID(),
          role: 'user',
          content: trimmed,
          createdAt: new Date().toISOString(),
        }

        set((state) => {
          state.messages.push(userMessage)
          state.isSending = true
          state.error = null
        })

        try {
          const { sessionId } = get()
          const { reply, affected_resources } = await bedrockApi.chat(sessionId, trimmed)

          set((state) => {
            state.messages.push({
              id: crypto.randomUUID(),
              role: 'assistant',
              content: reply,
              createdAt: new Date().toISOString(),
            })
            state.isSending = false
          })

          return affected_resources
        } catch (err) {
          set((state) => {
            state.isSending = false
            state.error = getErrorMessage(err)
          })
          return []
        }
      },

      clearConversation: () => {
        set((state) => {
          state.sessionId = newSessionId()
          state.messages = []
          state.error = null
        })
      },
    })),
    {
      name: 'bedrock-chat-store',
      partialize: (state) => ({ sessionId: state.sessionId, messages: state.messages }),
    }
  )
)
