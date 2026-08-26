import React from 'react'
import { AxiosError } from 'axios'
import { MapPin, Sparkles, UserCircle } from 'lucide-react'
import { useBedrockChat, useBedrockModel } from '@/hooks/useBedrockChat'
import { getAgentProfileLabel } from '@/config/agentProfiles'
import { CHAT_PROFILE_LABELS, resolveChatProfileKey } from '@/config/chatSectionProfiles'
import { BedrockChatSurface, BedrockPageContext } from '@/types/bedrock'
import { MessageList } from './MessageList'
import { ChatComposer } from './ChatComposer'
import { ConversationHistory } from './ConversationHistory'

const NotConfigured: React.FC = () => (
  <div className="card p-6 flex flex-col items-center text-center gap-3 flex-1 justify-center">
    <div
      className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ background: 'var(--primary-light)' }}
    >
      <Sparkles className="text-primary" size={22} aria-hidden="true" />
    </div>
    <h2 className="font-semibold text-text">Asistente IA</h2>
    <span className="badge badge-cyan">No configurado</span>
    <p className="text-text-secondary text-sm">
      Agent Bedrock todavía no está configurado en el servidor (faltan las credenciales de AWS o el harness).
    </p>
  </div>
)

interface ContextChipsProps {
  chatSurface: BedrockChatSurface
  pageContext?: BedrockPageContext | null
  agentLabel: string
}

/** Section location + specialist of this screen (model lives in the composer). */
const ContextChips: React.FC<ContextChipsProps> = ({ chatSurface, pageContext, agentLabel }) => {
  if (chatSurface === 'general') {
    return (
      <div className="flex flex-wrap gap-1.5 flex-shrink-0">
        <span className="badge badge-cyan text-[10px]">Chat general</span>
        <span className="inline-flex items-center gap-1 badge badge-slate text-[10px]">
          <UserCircle size={10} aria-hidden="true" />
          Orquestador
        </span>
      </div>
    )
  }

  if (!pageContext) return null

  const profileKey = resolveChatProfileKey(pageContext)

  return (
    <div className="flex flex-wrap gap-1.5 flex-shrink-0" aria-label="Contexto del chat">
      {pageContext.page_title && (
        <span className="inline-flex items-center gap-1 badge badge-slate text-[10px]">
          <MapPin size={10} aria-hidden="true" />
          {pageContext.page_title}
        </span>
      )}
      <span className="inline-flex items-center gap-1 badge badge-cyan text-[10px]" title="Agente de esta sección">
        <UserCircle size={10} aria-hidden="true" />
        {agentLabel}
      </span>
      {profileKey && CHAT_PROFILE_LABELS[profileKey] && (
        <span className="badge badge-slate text-[10px]">{CHAT_PROFILE_LABELS[profileKey]}</span>
      )}
    </div>
  )
}

export interface ChatWindowProps {
  /** `contextual` for sidebar, `general` for full-page orchestrator chat. */
  chatSurface?: BedrockChatSurface
  /** Current page context — required for contextual chat harness routing. */
  pageContext?: BedrockPageContext | null
  /** Show popover history controls in the header (false when page has its own list). */
  showHistoryControls?: boolean
}

/**
 * Bedrock chat panel: messages, section specialist chip, composer with model
 * picker, and optional conversation history popover.
 */
export const ChatWindow: React.FC<ChatWindowProps> = ({
  chatSurface = 'contextual',
  pageContext = null,
  showHistoryControls = true,
}) => {
  const {
    sessionId,
    messages,
    conversations,
    isSending,
    statusMessage,
    error,
    send,
    newConversation,
    switchConversation,
    renameConversation,
    deleteConversation,
    effectiveAgentProfileId,
  } = useBedrockChat({ chatSurface, pageContext })

  const { isError, error: modelError } = useBedrockModel()
  const isNotConfigured = isError && (modelError as AxiosError)?.response?.status === 503

  if (isNotConfigured) return <NotConfigured />

  return (
    <div className="flex-1 flex flex-col gap-3 min-h-0">
      {showHistoryControls && (
        <div className="flex items-center justify-end gap-2 flex-shrink-0">
          <ConversationHistory
            conversations={conversations}
            activeSessionId={sessionId}
            onSelect={switchConversation}
            onNew={newConversation}
            onRename={renameConversation}
            onDelete={deleteConversation}
            agentLabel={getAgentProfileLabel(effectiveAgentProfileId)}
          />
        </div>
      )}

      <ContextChips
        chatSurface={chatSurface}
        pageContext={pageContext}
        agentLabel={getAgentProfileLabel(effectiveAgentProfileId)}
      />

      <MessageList messages={messages} isSending={isSending} statusMessage={statusMessage} />

      {error && <p className="text-red-600 dark:text-red-400 text-xs flex-shrink-0">{error}</p>}

      <ChatComposer
        key={sessionId}
        sessionId={sessionId}
        pageContext={pageContext}
        onSend={send}
        disabled={isSending}
      />
    </div>
  )
}
