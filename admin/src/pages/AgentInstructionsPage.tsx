import React, { useEffect, useState } from 'react'
import { RotateCcw, Save } from 'lucide-react'
import { useBedrockInstructions, useBedrockInstructionsUpdate } from '@/hooks/useBedrockChat'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

export const AgentInstructionsPage: React.FC = () => {
  const { data, isLoading, isError, error } = useBedrockInstructions()
  const update = useBedrockInstructionsUpdate()
  const [draft, setDraft] = useState('')

  // Seed the textarea once the real value loads - a plain useEffect (not a
  // key-reset trick) since this only ever needs to happen once per mount,
  // not every time `data` changes (an in-flight edit shouldn't get clobbered
  // by a background refetch).
  useEffect(() => {
    if (data && draft === '') setDraft(data.system_prompt)
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  const isDirty = data !== undefined && draft !== data.system_prompt

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Instrucciones del Agente</h1>
        <p className="text-text-secondary mt-2">
          El system prompt que define cómo se comporta Agent Bedrock. Un cambio aquí aplica desde el siguiente
          mensaje, en cualquier conversación.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando instrucciones..." />}
      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

      {data && (
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h2 className="text-base font-semibold text-text">System Prompt</h2>
            {data.is_default && <span className="badge badge-cyan">Usando el predeterminado</span>}
          </div>
          <div className="card-body space-y-4">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={16}
              className="input-field text-sm font-mono leading-relaxed resize-y"
              aria-label="System prompt del agente"
            />
            {update.isError && (
              <p className="text-red-600 dark:text-red-400 text-xs">{getErrorMessage(update.error)}</p>
            )}
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="btn-primary flex items-center gap-2 disabled:opacity-50"
                disabled={!isDirty || update.isPending}
                onClick={() => update.mutate(draft)}
              >
                <Save size={15} aria-hidden="true" />
                Guardar
              </button>
              <button
                type="button"
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-text-secondary hover:bg-glass hover:text-text transition-colors disabled:opacity-50"
                disabled={data.is_default || update.isPending}
                onClick={() => {
                  update.mutate(null)
                  setDraft('')
                }}
              >
                <RotateCcw size={15} aria-hidden="true" />
                Restablecer al predeterminado
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
