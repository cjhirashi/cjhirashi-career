import React, { useEffect, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  Cpu,
  FileText,
  Loader2,
  Paperclip,
  Send,
  UserCircle,
  X,
} from 'lucide-react'
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

interface ComposerAttachment {
  localId: string
  file_id?: string
  filename: string
  mime_type?: string
  url?: string
  preview_url?: string
  uploading?: boolean
}

interface ChatComposerProps {
  sessionId: string
  chatSurface: BedrockChatSurface
  pageContext?: BedrockPageContext | null
  onSend: (text: string, attachments?: BedrockChatAttachment[]) => void
  disabled: boolean
}

const isImageMime = (mime?: string) => Boolean(mime?.startsWith('image/'))

const revokePreview = (previewUrl?: string) => {
  if (previewUrl?.startsWith('blob:')) URL.revokeObjectURL(previewUrl)
}

interface AttachmentPreviewProps {
  item: ComposerAttachment
  onRemove: () => void
}

const AttachmentPreview: React.FC<AttachmentPreviewProps> = ({ item, onRemove }) => {
  const imageSrc = item.preview_url ?? (isImageMime(item.mime_type) ? item.url : undefined)

  return (
    <div
      className="relative group w-[72px] h-[72px] rounded-xl overflow-hidden border flex-shrink-0"
      style={{ borderColor: 'var(--border-glass)', backgroundColor: 'var(--bg-glass)' }}
    >
      {imageSrc ? (
        <img src={imageSrc} alt="" className="w-full h-full object-cover" />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center gap-1 p-1.5">
          <FileText size={20} className="text-text-secondary flex-shrink-0" aria-hidden="true" />
          <span className="text-[9px] text-text-muted truncate w-full text-center leading-tight">
            {item.filename}
          </span>
        </div>
      )}
      {item.uploading && (
        <div className="absolute inset-0 bg-black/45 flex items-center justify-center">
          <Loader2 size={18} className="animate-spin text-white" aria-hidden="true" />
        </div>
      )}
      <button
        type="button"
        aria-label={`Quitar ${item.filename}`}
        onClick={onRemove}
        className="absolute top-1 right-1 p-0.5 rounded-md bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <X size={12} aria-hidden="true" />
      </button>
    </div>
  )
}

/**
 * Cursor-style chat input: attachments, textarea and controls live inside one box.
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
  const [attachments, setAttachments] = useState<ComposerAttachment[]>([])
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

  const readyAttachments = attachments.filter((a) => a.file_id && !a.uploading)
  const hasPendingUploads = attachments.some((a) => a.uploading)

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

  const removeAttachment = (localId: string) => {
    setAttachments((prev) => {
      const item = prev.find((a) => a.localId === localId)
      revokePreview(item?.preview_url)
      return prev.filter((a) => a.localId !== localId)
    })
  }

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length || uploading) return
    setUploadError(null)

    const slotsLeft = MAX_ATTACHMENTS - attachments.length
    const fileArray = Array.from(files).slice(0, slotsLeft)
    if (!fileArray.length) return

    setUploading(true)
    const pending: ComposerAttachment[] = fileArray.map((file) => ({
      localId: crypto.randomUUID(),
      filename: file.name,
      mime_type: file.type || undefined,
      preview_url: isImageMime(file.type) ? URL.createObjectURL(file) : undefined,
      uploading: true,
    }))
    setAttachments((prev) => [...prev, ...pending])

    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i]
      const { localId } = pending[i]
      try {
        if (file.size > MAX_FILE_MB * 1024 * 1024) {
          throw new Error(`"${file.name}" supera ${MAX_FILE_MB} MB`)
        }
        const uploaded = await filesApi.upload(file, {
          category: 'chat-attachment',
          isPublic: true,
          description: 'Adjunto de chat Agent Bedrock',
        })
        setAttachments((prev) =>
          prev.map((a) =>
            a.localId === localId
              ? {
                  ...a,
                  file_id: uploaded.id,
                  filename: uploaded.original_filename,
                  mime_type: uploaded.mime_type ?? a.mime_type,
                  url: uploaded.download_url ?? undefined,
                  uploading: false,
                }
              : a
          )
        )
      } catch (err) {
        setUploadError(getErrorMessage(err))
        setAttachments((prev) => {
          const item = prev.find((a) => a.localId === localId)
          revokePreview(item?.preview_url)
          return prev.filter((a) => a.localId !== localId)
        })
      }
    }

    setUploading(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const clearAttachments = () => {
    attachments.forEach((a) => revokePreview(a.preview_url))
    setAttachments([])
  }

  const submit = () => {
    const value = textareaRef.current?.value ?? ''
    if ((!value.trim() && readyAttachments.length === 0) || disabled || hasPendingUploads) return

    const payload: BedrockChatAttachment[] = readyAttachments.map(
      ({ localId, preview_url, uploading, ...rest }) => ({
        file_id: rest.file_id!,
        filename: rest.filename,
        mime_type: rest.mime_type,
        url: rest.url,
      })
    )
    onSend(value, payload.length ? payload : undefined)
    clearAttachments()
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

  const modelDropdown = (
    <div className="relative">
      <button
        type="button"
        onClick={() => setModelOpen((v) => !v)}
        disabled={disabled || !modelStatus}
        aria-haspopup="listbox"
        aria-expanded={modelOpen}
        title="Modelo para este turno"
        className="flex items-center gap-1 text-[11px] text-text-secondary hover:text-text px-2 py-1.5 rounded-lg hover:bg-glass transition-colors disabled:opacity-50"
      >
        <Cpu size={13} aria-hidden="true" />
        <span className="max-w-[130px] truncate">{selectedModel?.label ?? 'Modelo'}</span>
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
                    modelIdOverride:
                      model.model_id === modelStatus.current_model_id ? null : model.model_id,
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
  )

  const agentDropdown =
    chatSurface === 'contextual' ? (
      <div className="relative">
        <button
          type="button"
          onClick={() => setAgentOpen((v) => !v)}
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={agentOpen}
          title="Especialista (auto si no eliges)"
          className="flex items-center gap-1 text-[11px] text-text-secondary hover:text-text px-2 py-1.5 rounded-lg hover:bg-glass transition-colors disabled:opacity-50"
        >
          <UserCircle size={13} aria-hidden="true" />
          <span className="max-w-[110px] truncate">{selectedAgent?.label ?? 'Auto'}</span>
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
    ) : null

  return (
    <div className="flex flex-col gap-1.5 flex-shrink-0">
      <div
        className="rounded-2xl border transition-all focus-within:ring-2 focus-within:ring-cyan-500/60 focus-within:border-transparent"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-glass)',
          backdropFilter: 'blur(8px)',
        }}
      >
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 px-3 pt-3">
            {attachments.map((item) => (
              <AttachmentPreview
                key={item.localId}
                item={item}
                onRemove={() => removeAttachment(item.localId)}
              />
            ))}
          </div>
        )}

        <textarea
          ref={textareaRef}
          rows={MIN_ROWS}
          placeholder="Escribe un mensaje..."
          onInput={resizeTextarea}
          onKeyDown={handleKeyDown}
          disabled={disabled || hasPendingUploads}
          className="w-full resize-none bg-transparent text-sm text-text placeholder:text-text-muted px-3 pt-3 pb-1 focus:outline-none disabled:opacity-50"
          style={{ minHeight: '2.25rem', maxHeight: `${MAX_ROWS * 1.5}rem` }}
          aria-label="Mensaje para el asistente"
        />

        <div className="flex items-center justify-between gap-2 px-2 py-1.5">
          <div className="flex items-center gap-0.5 min-w-0">
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
              className="p-2 rounded-lg text-text-secondary hover:text-text hover:bg-glass transition-colors disabled:opacity-50"
            >
              <Paperclip size={16} aria-hidden="true" />
            </button>
            {modelDropdown}
            {agentDropdown}
          </div>

          <button
            type="button"
            onClick={submit}
            disabled={disabled || hasPendingUploads}
            aria-label="Enviar mensaje"
            title="Enviar mensaje"
            className="btn-primary p-2 rounded-xl flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={16} aria-hidden="true" />
          </button>
        </div>
      </div>

      {uploadError && <p className="text-red-600 dark:text-red-400 text-[10px] px-1">{uploadError}</p>}
      {modelStatus === undefined && (
        <p className="text-[10px] text-text-muted px-1">Cargando modelos…</p>
      )}
    </div>
  )
}
