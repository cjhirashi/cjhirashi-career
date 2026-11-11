import React, { useState } from 'react'
import { Brain, ChevronDown, ChevronRight } from 'lucide-react'
import { useBedrockConversations, useBedrockMemoryEvents } from '@/hooks/useBedrockChat'
import { getAgentProfileLabel } from '@/config/agentProfiles'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'
import { ThemedSelect } from '@/components/ThemedSelect'

const SectionCard: React.FC<{ title: string; subtitle?: string; icon: React.ElementType; children: React.ReactNode }> = ({
  title,
  subtitle,
  icon: Icon,
  children,
}) => (
  <div className="card">
    <div className="card-header">
      <h2 className="text-base font-semibold text-text flex items-center gap-2">
        <Icon size={17} className="text-primary" aria-hidden="true" />
        {title}
      </h2>
      {subtitle && <p className="text-text-secondary text-xs mt-1">{subtitle}</p>}
    </div>
    <div className="card-body">{children}</div>
  </div>
)

const EventsSection: React.FC = () => {
  const { data: conversations = [] } = useBedrockConversations()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const { data, isLoading, isError, error } = useBedrockMemoryEvents(sessionId)

  const toggle = (eventId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(eventId)) next.delete(eventId)
      else next.add(eventId)
      return next
    })
  }

  return (
    <SectionCard
      title="Eventos crudos de una conversación"
      subtitle="Historial PG de la conversación (Harness local) — mensajes user/assistant"
      icon={Brain}
    >
      {conversations.length === 0 ? (
        <p className="text-text-secondary text-sm text-center py-4">Todavía no tienes conversaciones.</p>
      ) : (
        <>
          <ThemedSelect
            value={sessionId ?? ''}
            onChange={(v) => setSessionId(v || null)}
            className="mb-4"
            aria-label="Elegir conversación"
            placeholder="Elige una conversación..."
            options={conversations.map((c) => {
              const surface = c.session_type === 'general' ? 'General' : 'Contextual'
              const agent = c.agent_profile_id
                ? getAgentProfileLabel(c.agent_profile_id)
                : 'sin agente'
              return { value: c.session_id, label: `${c.title} · ${surface} · ${agent}` }
            })}
          />

          {isLoading && <LoadingSpinner fullScreen={false} message="Cargando eventos..." />}
          {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}
          {sessionId && !isLoading && data?.length === 0 && (
            <p className="text-text-secondary text-sm text-center py-4">Sin eventos registrados todavía.</p>
          )}
          {data && data.length > 0 && (
            <div className="space-y-1.5">
              {data.map((event, i) => {
                const id = event.eventId ?? String(i)
                const isOpen = expanded.has(id)
                return (
                  <div key={id} className="rounded-xl bg-glass overflow-hidden">
                    <button
                      type="button"
                      onClick={() => toggle(id)}
                      className="w-full flex items-center justify-between gap-2 px-3 py-2 text-left"
                    >
                      <span className="text-xs font-mono text-text-secondary truncate">
                        {event.eventTimestamp ?? id}
                      </span>
                      {isOpen ? (
                        <ChevronDown size={14} className="flex-shrink-0 text-text-muted" aria-hidden="true" />
                      ) : (
                        <ChevronRight size={14} className="flex-shrink-0 text-text-muted" aria-hidden="true" />
                      )}
                    </button>
                    {isOpen && (
                      <pre className="text-[11px] whitespace-pre-wrap break-words text-text-secondary px-3 pb-3">
                        {JSON.stringify(event.payload ?? event, null, 2)}
                      </pre>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </SectionCard>
  )
}

export const AgentMemoryPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Memoria del Agente</h1>
        <p className="text-text-secondary mt-2">
          Historial de conversaciones en PostgreSQL (Harness local).
        </p>
      </div>
      <div className="space-y-6">
        <EventsSection />
      </div>
    </div>
  )
}
