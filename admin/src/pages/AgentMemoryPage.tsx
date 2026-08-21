import React, { useState } from 'react'
import { Brain, Search, ChevronDown, ChevronRight, Plus } from 'lucide-react'
import {
  useBedrockConversations,
  useBedrockManualMemory,
  useBedrockMemoryEvents,
  useBedrockMemoryRecords,
} from '@/hooks/useBedrockChat'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

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

const RecordsSection: React.FC = () => {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const { data, isLoading, isError, error } = useBedrockMemoryRecords(submittedQuery)

  return (
    <SectionCard
      title="Hechos que recuerda"
      subtitle="Búsqueda semántica sobre lo que el agente ha aprendido de tus conversaciones (memoria de largo plazo)"
      icon={Brain}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault()
          setSubmittedQuery(query)
        }}
        className="flex gap-2 mb-4"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ej. preferencias de vacantes, empresas de interés..."
          className="input-field flex-1"
        />
        <button type="submit" className="btn-primary flex items-center gap-2 flex-shrink-0">
          <Search size={15} aria-hidden="true" />
          Buscar
        </button>
      </form>

      {isLoading && <LoadingSpinner fullScreen={false} message="Buscando..." />}
      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}
      {!isLoading && submittedQuery && data?.length === 0 && (
        <p className="text-text-secondary text-sm text-center py-4">
          No se encontró nada. Esto puede pasar si la conversación fue muy reciente - AWS extrae hechos de forma
          asíncrona, no al instante.
        </p>
      )}
      {data && data.length > 0 && (
        <div className="space-y-2">
          {data.map((record, i) => (
            <div key={record.memoryRecordId ?? i} className="p-3 rounded-xl bg-glass">
              <pre className="text-xs whitespace-pre-wrap break-words text-text">
                {JSON.stringify(record.content ?? record, null, 2)}
              </pre>
              {typeof record.score === 'number' && (
                <p className="text-[11px] text-text-muted mt-1">relevancia: {record.score.toFixed(2)}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  )
}

const ManualMemorySection: React.FC = () => {
  const [text, setText] = useState('')
  const [savedAt, setSavedAt] = useState<number | null>(null)
  const manualMemory = useBedrockManualMemory()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    manualMemory.mutate(text.trim(), {
      onSuccess: () => {
        setText('')
        setSavedAt(Date.now())
      },
    })
  }

  return (
    <SectionCard
      title="Cargar una memoria manualmente"
      subtitle="Dile directamente al agente algo que debe recordar, sin tener que pasar por una conversación - AWS lo procesa de forma asíncrona, igual que un hecho extraído de un chat real"
      icon={Plus}
    >
      <form onSubmit={handleSubmit} className="space-y-3">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder="ej. Prefiero que las vacantes remotas siempre se marquen con track_category = remote"
          className="input-field text-sm"
        />
        {manualMemory.isError && (
          <p className="text-red-600 dark:text-red-400 text-xs">{getErrorMessage(manualMemory.error)}</p>
        )}
        {savedAt && !manualMemory.isPending && (
          <p className="text-xs text-text-secondary">
            Guardado - puede tardar unos minutos en aparecer en la búsqueda de "Hechos que recuerda".
          </p>
        )}
        <button
          type="submit"
          disabled={manualMemory.isPending || !text.trim()}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          <Plus size={15} aria-hidden="true" />
          Guardar memoria
        </button>
      </form>
    </SectionCard>
  )
}

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
      subtitle="El registro técnico exacto que el harness guardó en memoria - útil para confirmar qué se recordó de verdad"
      icon={Brain}
    >
      {conversations.length === 0 ? (
        <p className="text-text-secondary text-sm text-center py-4">Todavía no tienes conversaciones.</p>
      ) : (
        <>
          <select
            value={sessionId ?? ''}
            onChange={(e) => setSessionId(e.target.value || null)}
            className="input-field mb-4"
            aria-label="Elegir conversación"
          >
            <option value="">Elige una conversación...</option>
            {conversations.map((c) => (
              <option key={c.session_id} value={c.session_id}>
                {c.title}
              </option>
            ))}
          </select>

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
          Lo que Agent Bedrock recuerda de sus conversaciones, gestionado por AWS Bedrock AgentCore Memory.
        </p>
      </div>
      <div className="space-y-6">
        <ManualMemorySection />
        <RecordsSection />
        <EventsSection />
      </div>
    </div>
  )
}
