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
    const identity = useBedrockChatStore.getState().ensureSession('contextual', 'identity')
    const search = useBedrockChatStore.getState().ensureSession('contextual', 'search')
    const general = useBedrockChatStore.getState().ensureSession('general', 'orchestrator')

    expect(identity).not.toBe(search)
    expect(identity).not.toBe(general)
    expect(useBedrockChatStore.getState().activeSessionIds[conversationBucket('contextual', 'identity')]).toBe(
      identity
    )
    expect(useBedrockChatStore.getState().ensureSession('contextual', 'identity')).toBe(identity)
  })

  it('newConversation only rotates the current agent bucket', () => {
    const identity = useBedrockChatStore.getState().ensureSession('contextual', 'identity')
    const search = useBedrockChatStore.getState().ensureSession('contextual', 'search')

    useBedrockChatStore.getState().newConversation('contextual', 'identity')

    expect(useBedrockChatStore.getState().getActiveSessionId('contextual', 'identity')).not.toBe(identity)
    expect(useBedrockChatStore.getState().getActiveSessionId('contextual', 'search')).toBe(search)
  })
})
