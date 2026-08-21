import React, { useRef } from 'react'
import { Send } from 'lucide-react'

interface PromptInputProps {
  onSend: (text: string) => void
  disabled: boolean
}

export const PromptInput: React.FC<PromptInputProps> = ({ onSend, disabled }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const value = textareaRef.current?.value ?? ''
    if (!value.trim() || disabled) return
    onSend(value)
    if (textareaRef.current) textareaRef.current.value = ''
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex items-end gap-2 flex-shrink-0">
      <textarea
        ref={textareaRef}
        rows={1}
        placeholder="Escribe un mensaje..."
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className="input-field resize-none text-sm py-2 max-h-32"
        aria-label="Mensaje para el asistente"
      />
      <button
        type="button"
        onClick={submit}
        disabled={disabled}
        aria-label="Enviar mensaje"
        title="Enviar mensaje"
        className="btn-primary p-2.5 rounded-xl flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Send size={16} aria-hidden="true" />
      </button>
    </div>
  )
}
