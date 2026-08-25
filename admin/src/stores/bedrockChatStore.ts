import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import {
  AGENT_CHANGELOG,
  AGENT_DIGITAL_PRESENCE,
  AGENT_METHODOLOGIES,
  AGENT_NETWORKING,
  AGENT_ORCHESTRATOR,
  AGENT_PDF_DESIGN,
  AGENT_PDF_RENDER,
  AGENT_PROFESSIONAL_IDENTITY,
  AGENT_SEARCH_OPERATIONS,
  AGENT_SUPPORT,
  AGENT_TASK_MANAGER,
  AGENT_VISUAL_DESIGN,
} from '@/config/agentProfiles'
import { BedrockSessionType } from '@/types/bedrock'

/** One-shot persist migrate: localStorage buckets used pre-`agent_` ids. */
const LEGACY_PROFILE_IDS: Record<string, string> = {
  orchestrator: AGENT_ORCHESTRATOR,
  identity: AGENT_PROFESSIONAL_IDENTITY,
  search: AGENT_SEARCH_OPERATIONS,
  digital: AGENT_DIGITAL_PRESENCE,
  networking: AGENT_NETWORKING,
  support: AGENT_SUPPORT,
  methodologies: AGENT_METHODOLOGIES,
  pdf_design: AGENT_PDF_DESIGN,
  pdf_render: AGENT_PDF_RENDER,
  visual_design: AGENT_VISUAL_DESIGN,
  changelog: AGENT_CHANGELOG,
  task_manager: AGENT_TASK_MANAGER,
}

function canonicalPersistedProfileId(profileId: string): string {
  return LEGACY_PROFILE_IDS[profileId] ?? profileId
}

function remapLegacyAgentBuckets(ids: Record<string, string>): Record<string, string> {
  const next: Record<string, string> = {}
  for (const [key, sessionId] of Object.entries(ids)) {
    const colon = key.indexOf(':')
    if (colon === -1) continue
    const sessionType = key.slice(0, colon)
    const profileId = canonicalPersistedProfileId(key.slice(colon + 1))
    next[`${sessionType}:${profileId}`] = sessionId
  }
  return next
}

/** Harness local — session_id UUID; historial en PG. */
const newSessionId = () => crypto.randomUUID()

/** Persist key: one active session per surface + specialist. */
export function conversationBucket(sessionType: BedrockSessionType, agentProfileId: string): string {
  return `${sessionType}:${agentProfileId}`
}

/** Per-session overrides chosen in ChatComposer (not persisted server-side). */
export interface BedrockSessionPrefs {
  modelIdOverride?: string | null
}

type PersistedChatState = {
  activeSessionId?: string
  activeSessionIds?: Record<string, string>
  sessionPrefs?: Record<string, BedrockSessionPrefs>
  contextualAgentProfileId?: string | null
}

/**
 * Ephemeral chat UI state only - conversations and their messages are
 * server-persisted (see models/bedrock_conversation.py, api/bedrock.ts,
 * hooks/useBedrockChat.ts's React Query hooks) so they're the same on every
 * device, not just this one. Active session ids (one per agent) and per-session
 * composer prefs are kept here (persisted to localStorage) as per-device convenience.
 */
interface BedrockChatState {
  activeSessionIds: Record<string, string>
  sessionPrefs: Record<string, BedrockSessionPrefs>
  /** Explicit specialist in contextual chat; `null` = Auto (resolved from the page). */
  contextualAgentProfileId: string | null
  isSending: boolean
  /** Live progress for the in-flight turn (e.g. "Creando el registro...") -
   * streamed from the backend as it works, see api/bedrock.ts's `chat`. */
  statusMessage: string | null
  error: string | null

  setContextualAgentProfileId: (profileId: string | null) => void
  ensureSession: (sessionType: BedrockSessionType, agentProfileId: string) => string
  getActiveSessionId: (sessionType: BedrockSessionType, agentProfileId: string) => string | undefined
  newConversation: (sessionType: BedrockSessionType, agentProfileId: string) => void
  switchConversation: (sessionId: string, sessionType: BedrockSessionType, agentProfileId: string) => void
  getSessionPrefs: (sessionId: string) => BedrockSessionPrefs
  setSessionPrefs: (sessionId: string, prefs: Partial<BedrockSessionPrefs>) => void
}

export const useBedrockChatStore = create<BedrockChatState>()(
  persist(
    (set, get) => ({
      activeSessionIds: {
        [conversationBucket('general', AGENT_ORCHESTRATOR)]: newSessionId(),
      },
      sessionPrefs: {},
      contextualAgentProfileId: null,
      isSending: false,
      statusMessage: null,
      error: null,

      setContextualAgentProfileId: (profileId) => set({ contextualAgentProfileId: profileId }),

      ensureSession: (sessionType, agentProfileId) => {
        const key = conversationBucket(sessionType, agentProfileId)
        const existing = get().activeSessionIds[key]
        if (existing) return existing
        const id = newSessionId()
        set((state) => ({
          activeSessionIds: { ...state.activeSessionIds, [key]: id },
        }))
        return id
      },

      getActiveSessionId: (sessionType, agentProfileId) =>
        get().activeSessionIds[conversationBucket(sessionType, agentProfileId)],

      newConversation: (sessionType, agentProfileId) =>
        set((state) => ({
          activeSessionIds: {
            ...state.activeSessionIds,
            [conversationBucket(sessionType, agentProfileId)]: newSessionId(),
          },
          error: null,
        })),

      switchConversation: (sessionId, sessionType, agentProfileId) =>
        set((state) => ({
          activeSessionIds: {
            ...state.activeSessionIds,
            [conversationBucket(sessionType, agentProfileId)]: sessionId,
          },
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
      version: 3,
      migrate: (persisted, version) => {
        const legacy = persisted as PersistedChatState
        let activeSessionIds: Record<string, string> = { ...(legacy.activeSessionIds ?? {}) }

        if (legacy.activeSessionId && !legacy.activeSessionIds) {
          activeSessionIds = {
            contextual: legacy.activeSessionId,
            general: newSessionId(),
          }
        }

        if (version < 2) {
          const next: Record<string, string> = {}
          const generalId =
            activeSessionIds[conversationBucket('general', AGENT_ORCHESTRATOR)] ??
            activeSessionIds['general:orchestrator'] ??
            activeSessionIds.general
          if (generalId) next[conversationBucket('general', AGENT_ORCHESTRATOR)] = generalId
          activeSessionIds = next
        }

        if (version < 3) {
          activeSessionIds = remapLegacyAgentBuckets(activeSessionIds)
        }

        const contextual = legacy.contextualAgentProfileId
        return {
          activeSessionIds,
          sessionPrefs: legacy.sessionPrefs ?? {},
          contextualAgentProfileId: contextual ? canonicalPersistedProfileId(contextual) : null,
        }
      },
      partialize: (state) => ({
        activeSessionIds: state.activeSessionIds,
        sessionPrefs: state.sessionPrefs,
        contextualAgentProfileId: state.contextualAgentProfileId,
      }),
    }
  )
)
