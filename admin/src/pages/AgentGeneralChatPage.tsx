import React, { useState } from 'react'
import { Check, MessageCircle, Pencil, Plus, Trash2, X } from 'lucide-react'
import { ChatWindow } from '@/components/bedrock/ChatWindow'
import { useBedrockChat } from '@/hooks/useBedrockChat'
import { useChatPageContext } from '@/hooks/useChatPageContext'

const relativeTime = (iso: string): string => {
  const diffMs = Date.now() - new Date(iso).getTime()
  const minutes = Math.round(diffMs / 60_000)
  if (minutes < 1) return 'ahora'
  if (minutes < 60) return `hace ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `hace ${hours} h`
  const days = Math.round(hours / 24)
  return `hace ${days} d`
}

/**
 * Full-page general chat with the orchestrator agent. Conversations are
 * filtered to `session_type=general` and `agent_profile_id=agent_orchestrator`.
 */
export const AgentGeneralChatPage: React.FC = () => {
  const pageContext = useChatPageContext()
  const {
    sessionId,
    conversations,
    newConversation,
    switchConversation,
    renameConversation,
    deleteConversation,
  } = useBedrockChat({ chatSurface: 'general', pageContext })

  const [editingId, setEditingId] = useState<string | null>(null)
  const [draftTitle, setDraftTitle] = useState('')

  const startEditing = (id: string, title: string) => {
    setEditingId(id)
    setDraftTitle(title)
  }

  const commitRename = (id: string) => {
    if (draftTitle.trim()) renameConversation(id, draftTitle.trim())
    setEditingId(null)
  }

  const handleDelete = (id: string, title: string) => {
    if (window.confirm(`¿Eliminar la conversación "${title}"? Esta acción no se puede deshacer.`)) {
      deleteConversation(id)
    }
  }

  return (
    <div className="flex flex-col gap-4 h-full min-h-0">
      <div className="flex items-center gap-2 flex-shrink-0">
        <MessageCircle size={22} className="text-primary" aria-hidden="true" />
        <div>
          <h1 className="text-xl font-semibold text-text">Chat General</h1>
          <p className="text-text-secondary text-sm">
            Orquestador con acceso a todos los dominios — puede delegar a especialistas.
          </p>
        </div>
      </div>

      <div className="flex flex-1 gap-4 min-h-0">
        {/* Conversation list — general sessions only */}
        <aside className="card w-64 flex-shrink-0 flex flex-col min-h-0 hidden md:flex">
          <div className="card-header flex items-center justify-between gap-2 py-3">
            <h2 className="text-sm font-semibold text-text">Conversaciones</h2>
            <button
              type="button"
              onClick={newConversation}
              aria-label="Nueva conversación"
              title="Nueva conversación"
              className="p-1.5 rounded-lg text-text-secondary hover:bg-glass hover:text-text transition-colors"
            >
              <Plus size={15} aria-hidden="true" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {conversations.length === 0 ? (
              <p className="text-xs text-text-secondary text-center py-4">Sin conversaciones aún.</p>
            ) : (
              conversations.map((conversation) => {
                const isActive = conversation.session_id === sessionId
                const isEditing = editingId === conversation.session_id
                return (
                  <div
                    key={conversation.session_id}
                    className={`group rounded-xl transition-colors ${isActive && !isEditing ? 'bg-glass' : ''}`}
                  >
                    {isEditing ? (
                      <div className="flex items-center gap-1 px-2 py-1">
                        <input
                          autoFocus
                          value={draftTitle}
                          onChange={(e) => setDraftTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') commitRename(conversation.session_id)
                            if (e.key === 'Escape') setEditingId(null)
                          }}
                          className="input-field text-xs py-1 flex-1"
                          aria-label="Nuevo título"
                        />
                        <button
                          type="button"
                          onClick={() => commitRename(conversation.session_id)}
                          aria-label="Guardar"
                          className="p-1 rounded-lg text-primary hover:bg-glass"
                        >
                          <Check size={13} aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingId(null)}
                          aria-label="Cancelar"
                          className="p-1 rounded-lg text-text-secondary hover:bg-glass"
                        >
                          <X size={13} aria-hidden="true" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-0.5">
                        <button
                          type="button"
                          onClick={() => switchConversation(conversation.session_id)}
                          className={`flex-1 min-w-0 text-left px-3 py-2 text-sm transition-colors ${
                            isActive ? 'text-text' : 'text-text-secondary hover:text-text'
                          }`}
                        >
                          <p className="truncate">{conversation.title}</p>
                          <p className="text-[10px] text-text-muted">{relativeTime(conversation.updated_at)}</p>
                        </button>
                        <button
                          type="button"
                          onClick={() => startEditing(conversation.session_id, conversation.title)}
                          aria-label="Renombrar"
                          title="Renombrar"
                          className="p-1 rounded-lg text-text-muted opacity-0 group-hover:opacity-100 hover:bg-glass hover:text-text transition-opacity"
                        >
                          <Pencil size={12} aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(conversation.session_id, conversation.title)}
                          aria-label="Eliminar"
                          title="Eliminar"
                          className="p-1 mr-1 rounded-lg text-text-muted opacity-0 group-hover:opacity-100 hover:bg-glass hover:text-red-500 transition-opacity"
                        >
                          <Trash2 size={12} aria-hidden="true" />
                        </button>
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </aside>

        {/* Chat area */}
        <div className="card flex-1 flex flex-col min-h-0 p-4">
          <ChatWindow
            chatSurface="general"
            pageContext={pageContext}
            showHistoryControls={false}
          />
        </div>
      </div>
    </div>
  )
}
