import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { BedrockSessionType } from '@/types/bedrock'

/** Harness local — session_id UUID; historial en PG. */
const newSessionId = () => crypto.randomUUID()

/** Per-session overrides chosen in ChatComposer (not persisted server-side). */
export interface BedrockSessionPrefs {
  modelIdOverride?: string | null
  agentProfileIdOverride?: string | null
}

/**
 * Ephemeral chat UI state only - conversations and their messages are
 * server-persisted (see models/bedrock_conversation.py, api/bedrock.ts,
 * hooks/useBedrockChat.ts's React Query hooks) so they're the same on every
 * device, not just this one. Active session ids and per-session composer
 * prefs are kept here (persisted to localStorage) as per-device convenience.
 */
interface BedrockChatState {
  activeSessionIds: Record<BedrockSessionType, string>
  sessionPrefs: Record<string, BedrockSessionPrefs>
  isSending: boolean
  /** Live progress for the in-flight turn (e.g. "Creando el registro...") -
   * streamed from the backend as it works, see api/bedrock.ts's `chat`. */
  statusMessage: string | null
  error: string | null

  getActiveSessionId: (sessionType: BedrockSessionType) => string
  newConversation: (sessionType?: BedrockSessionType) => void
  switchConversation: (sessionId: string, sessionType?: BedrockSessionType) => void
  getSessionPrefs: (sessionId: string) => BedrockSessionPrefs
  setSessionPrefs: (sessionId: string, prefs: Partial<BedrockSessionPrefs>) => void
}

export const useBedrockChatStore = create<BedrockChatState>()(
  persist(
    (set, get) => ({
      activeSessionIds: {
        contextual: newSessionId(),
        general: newSessionId(),
      },
      sessionPrefs: {},
      isSending: false,
      statusMessage: null,
      error: null,

      getActiveSessionId: (sessionType) => get().activeSessionIds[sessionType],

      newConversation: (sessionType = 'contextual') =>
        set((state) => ({
          activeSessionIds: { ...state.activeSessionIds, [sessionType]: newSessionId() },
          error: null,
        })),

      switchConversation: (sessionId, sessionType = 'contextual') =>
        set((state) => ({
          activeSessionIds: { ...state.activeSessionIds, [sessionType]: sessionId },
          error: null,
        })),

      getSessionPrefs: (sessionId) => get().sessionPrefs[sessionId] ?? {},

      setSessionPrefs: (sessionId, prefs) =>
        set((state) => ({
          sessionPrefs: {
            ...state.sessionPrefs,
            [sessionId]: { ...state.sessionPrefs[sessionId], ...prefs },
          },
        })),
    }),
    {
      name: 'bedrock-chat-store',
      version: 1,
      migrate: (persisted) => {
        const legacy = persisted as { activeSessionId?: string; activeSessionIds?: Record<BedrockSessionType, string> }
        if (legacy.activeSessionId && !legacy.activeSessionIds) {
          return {
            ...legacy,
            activeSessionIds: {
              contextual: legacy.activeSessionId,
              general: newSessionId(),
            },
          }
        }
        return persisted
      },
      partialize: (state) => ({
        activeSessionIds: state.activeSessionIds,
        sessionPrefs: state.sessionPrefs,
      }),
    }
  )
)
