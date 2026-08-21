import React, { useState } from 'react'
import { Check, History, Pencil, Plus, Trash2, X } from 'lucide-react'
import { BedrockConversation } from '@/types/bedrock'

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

interface ConversationHistoryProps {
  conversations: BedrockConversation[]
  activeSessionId: string
  onSelect: (sessionId: string) => void
  onNew: () => void
  onRename: (sessionId: string, title: string) => void
  onDelete: (sessionId: string) => void
}

/** Past conversations, server-persisted (see hooks/useBedrockChat.ts) - same
 * popover pattern as `ModelSelector`/`Navbar`'s user menu, so it matches the
 * app's dark theme instead of a native picker. */
export const ConversationHistory: React.FC<ConversationHistoryProps> = ({
  conversations,
  activeSessionId,
  onSelect,
  onNew,
  onRename,
  onDelete,
}) => {
  const [open, setOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [draftTitle, setDraftTitle] = useState('')

  const startEditing = (sessionId: string, currentTitle: string) => {
    setEditingId(sessionId)
    setDraftTitle(currentTitle)
  }

  const commitRename = (sessionId: string) => {
    if (draftTitle.trim()) onRename(sessionId, draftTitle)
    setEditingId(null)
  }

  const handleDelete = (sessionId: string, title: string) => {
    if (window.confirm(`¿Eliminar la conversación "${title}"? Esta acción no se puede deshacer.`)) {
      onDelete(sessionId)
    }
  }

  return (
    <div className="relative flex items-center gap-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="true"
        aria-expanded={open}
        aria-label="Historial de conversaciones"
        title="Historial de conversaciones"
        className="p-1.5 rounded-lg text-text-secondary hover:bg-glass hover:text-text transition-colors flex-shrink-0"
      >
        <History size={15} aria-hidden="true" />
      </button>
      <button
        type="button"
        onClick={onNew}
        aria-label="Nueva conversación"
        title="Nueva conversación"
        className="p-1.5 rounded-lg text-text-secondary hover:bg-glass hover:text-text transition-colors flex-shrink-0"
      >
        <Plus size={15} aria-hidden="true" />
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => {
              setOpen(false)
              setEditingId(null)
            }}
          />
          <div
            className="absolute right-0 top-full mt-2 w-80 max-w-[85vw] max-h-96 overflow-y-auto z-50 rounded-2xl border shadow-glass"
            style={{ backgroundColor: 'var(--bg-popover)', borderColor: 'var(--border-glass)', backdropFilter: 'blur(16px)' }}
          >
            {conversations.length === 0 ? (
              <p className="p-4 text-sm text-text-secondary text-center">Todavía no tienes conversaciones.</p>
            ) : (
              <div className="p-1.5">
                {conversations.map((conversation) => {
                  const isEditing = editingId === conversation.session_id
                  return (
                    <div
                      key={conversation.session_id}
                      className={`group flex items-center gap-1 rounded-xl transition-colors ${
                        conversation.session_id === activeSessionId && !isEditing ? 'bg-glass' : ''
                      }`}
                    >
                      {isEditing ? (
                        <div className="flex-1 flex items-center gap-1 px-2 py-1">
                          <input
                            autoFocus
                            value={draftTitle}
                            onChange={(e) => setDraftTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') commitRename(conversation.session_id)
                              if (e.key === 'Escape') setEditingId(null)
                            }}
                            className="input-field text-sm py-1 flex-1"
                            aria-label="Nuevo título de la conversación"
                          />
                          <button
                            type="button"
                            onClick={() => commitRename(conversation.session_id)}
                            aria-label="Guardar"
                            title="Guardar"
                            className="p-1.5 rounded-lg text-primary hover:bg-glass flex-shrink-0"
                          >
                            <Check size={14} aria-hidden="true" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditingId(null)}
                            aria-label="Cancelar"
                            title="Cancelar"
                            className="p-1.5 rounded-lg text-text-secondary hover:bg-glass flex-shrink-0"
                          >
                            <X size={14} aria-hidden="true" />
                          </button>
                        </div>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => {
                              onSelect(conversation.session_id)
                              setOpen(false)
                            }}
                            className={`flex-1 min-w-0 text-left px-3 py-2 text-sm transition-colors ${
                              conversation.session_id === activeSessionId ? 'text-text' : 'text-text-secondary hover:text-text'
                            }`}
                          >
                            <p className="truncate">{conversation.title}</p>
                            <p className="text-[11px] text-text-muted">{relativeTime(conversation.updated_at)}</p>
                          </button>
                          <button
                            type="button"
                            onClick={() => startEditing(conversation.session_id, conversation.title)}
                            aria-label="Renombrar conversación"
                            title="Renombrar"
                            className="p-1.5 rounded-lg text-text-muted opacity-100 md:opacity-0 md:group-hover:opacity-100 hover:bg-glass hover:text-text transition-opacity flex-shrink-0"
                          >
                            <Pencil size={13} aria-hidden="true" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(conversation.session_id, conversation.title)}
                            aria-label="Eliminar conversación"
                            title="Eliminar"
                            className="p-1.5 mr-1 rounded-lg text-text-muted opacity-100 md:opacity-0 md:group-hover:opacity-100 hover:bg-glass hover:text-red-500 transition-opacity flex-shrink-0"
                          >
                            <Trash2 size={13} aria-hidden="true" />
                          </button>
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
