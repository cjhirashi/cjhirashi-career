import React, { useEffect, useRef, useState } from 'react'
import { Check, ChevronDown, Cpu, Paperclip, Send, UserCircle, X } from 'lucide-react'
import { useBedrockModel } from '@/hooks/useBedrockChat'
import { useBedrockChatStore } from '@/stores/bedrockChatStore'
import { CONTEXTUAL_AGENT_PROFILES } from '@/config/agentProfiles'
import { resolveRecommendedModel } from '@/config/chatSectionProfiles'
import { filesApi } from '@/api/files'
import { BedrockChatAttachment, BedrockChatSurface, BedrockPageContext } from '@/types/bedrock'
import { getErrorMessage } from '@/utils/errors'

const MIN_ROWS = 1
const MAX_ROWS = 6
const MAX_ATTACHMENTS = 3
const MAX_FILE_MB = 5

interface ChatComposerProps {
  sessionId: string
  chatSurface: BedrockChatSurface
  pageContext?: BedrockPageContext | null
  onSend: (text: string, attachments?: BedrockChatAttachment[]) => void
  disabled: boolean
}

/**
 * Rich chat input: auto-growing textarea, model/agent override, file attachments.
 */
export const ChatComposer: React.FC<ChatComposerProps> = ({
  sessionId,
  chatSurface,
  pageContext,
  onSend,
  disabled,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [modelOpen, setModelOpen] = useState(false)
  const [agentOpen, setAgentOpen] = useState(false)
  const [attachments, setAttachments] = useState<BedrockChatAttachment[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const { data: modelStatus } = useBedrockModel()
  const sessionPrefs = useBedrockChatStore((s) => s.getSessionPrefs(sessionId))
  const setSessionPrefs = useBedrockChatStore((s) => s.setSessionPrefs)

  const defaultModelId =
    sessionPrefs.modelIdOverride ??
    resolveRecommendedModel(pageContext, modelStatus?.current_model_id)

  const selectedModel =
    modelStatus?.available_models.find((m) => m.model_id === defaultModelId) ??
    modelStatus?.available_models.find((m) => m.model_id === modelStatus.current_model_id)

  const selectedAgent = CONTEXTUAL_AGENT_PROFILES.find(
    (p) => p.id === sessionPrefs.agentProfileIdOverride
  )

  const resizeTextarea = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const lineHeight = parseInt(getComputedStyle(el).lineHeight, 10) || 20
    const maxHeight = lineHeight * MAX_ROWS
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`
  }

  useEffect(() => {
    resizeTextarea()
  }, [])

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length || uploading) return
    setUploadError(null)
    setUploading(true)
    try {
      const next: BedrockChatAttachment[] = [...attachments]
      for (const file of Array.from(files)) {
        if (next.length >= MAX_ATTACHMENTS) break
        if (file.size > MAX_FILE_MB * 1024 * 1024) {
          throw new Error(`"${file.name}" supera ${MAX_FILE_MB} MB`)
        }
        const uploaded = await filesApi.upload(file, {
          category: 'chat-attachment',
          isPublic: true,
          description: 'Adjunto de chat Agent Bedrock',
        })
        next.push({
          file_id: uploaded.id,
          filename: uploaded.original_filename,
          mime_type: uploaded.mime_type ?? undefined,
          url: uploaded.download_url ?? undefined,
        })
      }
      setAttachments(next)
    } catch (err) {
      setUploadError(getErrorMessage(err))
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const submit = () => {
    const value = textareaRef.current?.value ?? ''
    if ((!value.trim() && attachments.length === 0) || disabled || uploading) return
    onSend(value, attachments.length ? attachments : undefined)
    setAttachments([])
    if (textareaRef.current) {
      textareaRef.current.value = ''
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex flex-col gap-2 flex-shrink-0">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <button
            type="button"
            onClick={() => setModelOpen((v) => !v)}
            disabled={disabled || !modelStatus}
            aria-haspopup="listbox"
            aria-expanded={modelOpen}
            title="Modelo para este turno"
            className="flex items-center gap-1 text-[11px] text-text-secondary hover:text-text px-2 py-1 rounded-lg hover:bg-glass transition-colors disabled:opacity-50"
          >
            <Cpu size={12} aria-hidden="true" />
            <span className="max-w-[120px] truncate">{selectedModel?.label ?? 'Modelo'}</span>
            <ChevronDown size={11} aria-hidden="true" />
          </button>
          {modelOpen && modelStatus && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setModelOpen(false)} />
              <div
                className="absolute left-0 bottom-full mb-1 w-56 z-50 rounded-2xl border shadow-glass overflow-hidden max-h-48 overflow-y-auto"
                style={{
                  backgroundColor: 'var(--bg-popover)',
                  borderColor: 'var(--border-glass)',
                  backdropFilter: 'blur(16px)',
                }}
                role="listbox"
                aria-label="Seleccionar modelo"
              >
                {modelStatus.available_models.map((model) => (
                  <button
                    key={model.model_id}
                    type="button"
                    role="option"
                    aria-selected={model.model_id === defaultModelId}
                    onClick={() => {
                      setSessionPrefs(sessionId, {
                        modelIdOverride: model.model_id === modelStatus.current_model_id ? null : model.model_id,
                      })
                      setModelOpen(false)
                    }}
                    className="w-full flex items-center justify-between gap-2 px-3 py-2 text-xs text-text hover:bg-glass transition-colors text-left"
                  >
                    <span>{model.label}</span>
                    {model.model_id === defaultModelId && (
                      <Check size={12} className="text-primary flex-shrink-0" aria-hidden="true" />
                    )}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {chatSurface === 'contextual' && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setAgentOpen((v) => !v)}
              disabled={disabled}
              aria-haspopup="listbox"
              aria-expanded={agentOpen}
              title="Especialista (auto si no eliges)"
              className="flex items-center gap-1 text-[11px] text-text-secondary hover:text-text px-2 py-1 rounded-lg hover:bg-glass transition-colors disabled:opacity-50"
            >
              <UserCircle size={12} aria-hidden="true" />
              <span className="max-w-[120px] truncate">{selectedAgent?.label ?? 'Auto'}</span>
              <ChevronDown size={11} aria-hidden="true" />
            </button>
            {agentOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setAgentOpen(false)} />
                <div
                  className="absolute left-0 bottom-full mb-1 w-52 z-50 rounded-2xl border shadow-glass overflow-hidden max-h-48 overflow-y-auto"
                  style={{
                    backgroundColor: 'var(--bg-popover)',
                    borderColor: 'var(--border-glass)',
                    backdropFilter: 'blur(16px)',
                  }}
                  role="listbox"
                  aria-label="Seleccionar especialista"
                >
                  <button
                    type="button"
                    role="option"
                    aria-selected={!sessionPrefs.agentProfileIdOverride}
                    onClick={() => {
                      setSessionPrefs(sessionId, { agentProfileIdOverride: null })
                      setAgentOpen(false)
                    }}
                    className="w-full flex items-center justify-between gap-2 px-3 py-2 text-xs text-text hover:bg-glass transition-colors text-left"
                  >
                    <span>Auto (por pantalla)</span>
                    {!sessionPrefs.agentProfileIdOverride && (
                      <Check size={12} className="text-primary flex-shrink-0" aria-hidden="true" />
                    )}
                  </button>
                  {CONTEXTUAL_AGENT_PROFILES.map((profile) => (
                    <button
                      key={profile.id}
                      type="button"
                      role="option"
                      aria-selected={profile.id === sessionPrefs.agentProfileIdOverride}
                      onClick={() => {
                        setSessionPrefs(sessionId, { agentProfileIdOverride: profile.id })
                        setAgentOpen(false)
                      }}
                      className="w-full flex items-center justify-between gap-2 px-3 py-2 text-xs text-text hover:bg-glass transition-colors text-left"
                    >
                      <span>{profile.label}</span>
                      {profile.id === sessionPrefs.agentProfileIdOverride && (
                        <Check size={12} className="text-primary flex-shrink-0" aria-hidden="true" />
                      )}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          multiple
          accept="image/*,.pdf,.txt,.md,.json"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <button
          type="button"
          disabled={disabled || uploading || attachments.length >= MAX_ATTACHMENTS}
          title="Adjuntar imagen, PDF o texto"
          aria-label="Adjuntar archivo"
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-1 text-[11px] text-text-secondary hover:text-text px-2 py-1 rounded-lg hover:bg-glass transition-colors disabled:opacity-50"
        >
          <Paperclip size={12} aria-hidden="true" />
          <span>{uploading ? 'Subiendo…' : 'Adjuntar'}</span>
        </button>
      </div>

      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {attachments.map((a) => (
            <span
              key={a.file_id}
              className="inline-flex items-center gap-1 text-[10px] badge badge-slate max-w-[180px]"
            >
              <span className="truncate">{a.filename}</span>
              <button
                type="button"
                aria-label={`Quitar ${a.filename}`}
                onClick={() => setAttachments((prev) => prev.filter((x) => x.file_id !== a.file_id))}
              >
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}
      {uploadError && <p className="text-red-600 dark:text-red-400 text-[10px]">{uploadError}</p>}

      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          rows={MIN_ROWS}
          placeholder="Escribe un mensaje..."
          onInput={resizeTextarea}
          onKeyDown={handleKeyDown}
          disabled={disabled || uploading}
          className="input-field resize-none text-sm py-2 flex-1"
          style={{ minHeight: '2.5rem', maxHeight: `${MAX_ROWS * 1.5}rem` }}
          aria-label="Mensaje para el asistente"
        />
        <button
          type="button"
          onClick={submit}
          disabled={disabled || uploading}
          aria-label="Enviar mensaje"
          title="Enviar mensaje"
          className="btn-primary p-2.5 rounded-xl flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={16} aria-hidden="true" />
        </button>
      </div>

      {modelStatus === undefined && (
        <p className="text-[10px] text-text-muted">Cargando modelos…</p>
      )}
    </div>
  )
}
