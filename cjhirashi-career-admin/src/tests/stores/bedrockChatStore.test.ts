import { describe, it, expect, beforeEach } from 'vitest'
import { conversationBucket, useBedrockChatStore } from '@/stores/bedrockChatStore'

describe('bedrockChatStore', () => {
  beforeEach(() => {
    useBedrockChatStore.setState({
      activeSessionIds: {},
      sessionPrefs: {},
      contextualAgentProfileId: null,
      isSending: false,
      statusMessage: null,
      error: null,
    })
  })

  it('keeps a distinct session id per specialist', () => {
    const identity = useBedrockChatStore.getState().ensureSession('contextual', 'agent_professional_identity')
    const search = useBedrockChatStore.getState().ensureSession('contextual', 'agent_search_operations')
    const general = useBedrockChatStore.getState().ensureSession('general', 'agent_orchestrator')

    expect(identity).not.toBe(search)
    expect(identity).not.toBe(general)
    expect(useBedrockChatStore.getState().activeSessionIds[conversationBucket('contextual', 'agent_professional_identity')]).toBe(
      identity
    )
    expect(useBedrockChatStore.getState().ensureSession('contextual', 'agent_professional_identity')).toBe(identity)
  })

  it('newConversation only rotates the current agent bucket', () => {
    const identity = useBedrockChatStore.getState().ensureSession('contextual', 'agent_professional_identity')
    const search = useBedrockChatStore.getState().ensureSession('contextual', 'agent_search_operations')

    useBedrockChatStore.getState().newConversation('contextual', 'agent_professional_identity')

    expect(useBedrockChatStore.getState().getActiveSessionId('contextual', 'agent_professional_identity')).not.toBe(identity)
    expect(useBedrockChatStore.getState().getActiveSessionId('contextual', 'agent_search_operations')).toBe(search)
  })
})
