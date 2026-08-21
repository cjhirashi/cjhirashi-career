import React, { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Sparkles, User } from 'lucide-react'
import { BedrockChatMessage } from '@/types/bedrock'

const Bubble: React.FC<{ message: BedrockChatMessage }> = ({ message }) => {
  const isUser = message.role === 'user'
  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ background: isUser ? 'var(--glass-bg)' : 'var(--primary-light)' }}
      >
        {isUser ? (
          <User size={14} className="text-text-secondary" aria-hidden="true" />
        ) : (
          <Sparkles size={14} className="text-primary" aria-hidden="true" />
        )}
      </div>
      <div
        className={`rounded-2xl px-3 py-2 text-sm max-w-[85%] ${
          isUser ? 'bg-primary text-white' : 'bg-glass text-text'
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <div className="markdown-body markdown-body-compact">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

const TypingIndicator: React.FC = () => (
  <div className="flex gap-2">
    <div
      className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ background: 'var(--primary-light)' }}
    >
      <Sparkles size={14} className="text-primary" aria-hidden="true" />
    </div>
    <div className="rounded-2xl px-3 py-2 bg-glass flex items-center gap-1">
      <span className="typing-dot" />
      <span className="typing-dot" style={{ animationDelay: '0.15s' }} />
      <span className="typing-dot" style={{ animationDelay: '0.3s' }} />
    </div>
  </div>
)

interface MessageListProps {
  messages: BedrockChatMessage[]
  isSending: boolean
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isSending }) => {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isSending])

  if (messages.length === 0 && !isSending) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 py-6">
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ background: 'var(--primary-light)' }}
        >
          <Sparkles className="text-primary" size={22} aria-hidden="true" />
        </div>
        <p className="text-text-secondary text-sm max-w-[85%]">
          Pregúntame lo que necesites sobre tu carrera - puedo leer y escribir directamente en tus tablas.
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto flex flex-col gap-3 py-2">
      {messages.map((message) => (
        <Bubble key={message.id} message={message} />
      ))}
      {isSending && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  )
}
