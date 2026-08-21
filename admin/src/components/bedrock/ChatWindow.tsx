import React from 'react'
import { AxiosError } from 'axios'
import { Sparkles, Trash2 } from 'lucide-react'
import { useBedrockChat, useBedrockModel } from '@/hooks/useBedrockChat'
import { MessageList } from './MessageList'
import { PromptInput } from './PromptInput'
import { ModelSelector } from './ModelSelector'

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

export const ChatWindow: React.FC = () => {
  const { messages, isSending, error, send, clearConversation } = useBedrockChat()
  // Reuses the model-status query as a lightweight "is Bedrock configured?"
  // probe - a 503 here means the whole feature is off, not just this query.
  const { isError, error: modelError } = useBedrockModel()

  const isNotConfigured = isError && (modelError as AxiosError)?.response?.status === 503

  if (isNotConfigured) return <NotConfigured />

  return (
    <div className="flex-1 flex flex-col gap-3 min-h-0">
      <div className="flex items-center justify-between gap-2 flex-shrink-0">
        <ModelSelector />
        <button
          type="button"
          onClick={clearConversation}
          disabled={messages.length === 0}
          aria-label="Nueva conversación"
          title="Nueva conversación"
          className="p-1.5 rounded-lg text-text-secondary hover:bg-glass hover:text-text transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
        >
          <Trash2 size={15} aria-hidden="true" />
        </button>
      </div>

      <MessageList messages={messages} isSending={isSending} />

      {error && <p className="text-red-600 dark:text-red-400 text-xs flex-shrink-0">{error}</p>}

      <PromptInput onSend={send} disabled={isSending} />
    </div>
  )
}
