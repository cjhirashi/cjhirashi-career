import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/** AgentCore Harness requires `runtimeSessionId` to be at least 33
 * characters - `crypto.randomUUID()` (36 chars) comfortably clears that. */
const newSessionId = () => crypto.randomUUID()

/**
 * Ephemeral chat UI state only - conversations and their messages are
 * server-persisted (see models/bedrock_conversation.py, api/bedrock.ts,
 * hooks/useBedrockChat.ts's React Query hooks) so they're the same on every
 * device, not just this one. Only `activeSessionId` is kept here (and
 * persisted to localStorage) - "which conversation was open" is a
 * per-device convenience, not data that needs to sync.
 */
interface BedrockChatState {
  activeSessionId: string
  isSending: boolean
  /** Live progress for the in-flight turn (e.g. "Creando el registro...") -
   * streamed from the backend as it works, see api/bedrock.ts's `chat`. */
  statusMessage: string | null
  error: string | null

  newConversation: () => void
  switchConversation: (sessionId: string) => void
}

export const useBedrockChatStore = create<BedrockChatState>()(
  persist(
    (set) => ({
      activeSessionId: newSessionId(),
      isSending: false,
      statusMessage: null,
      error: null,

      newConversation: () => set({ activeSessionId: newSessionId(), error: null }),
      switchConversation: (sessionId: string) => set({ activeSessionId: sessionId, error: null }),
    }),
    {
      name: 'bedrock-chat-store',
      partialize: (state) => ({ activeSessionId: state.activeSessionId }),
    }
  )
)
