import React, { useEffect, useState } from 'react'
import { RotateCcw, Save } from 'lucide-react'
import {
  useBedrockInstructions,
  useBedrockInstructionsUpdate,
  useBedrockGlobalRulesUpdate,
} from '@/hooks/useBedrockChat'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

/**
 * Two globals that apply to every agent, regardless of specialty:
 * - System prompt: the base instructions prepended to every agent's context.
 * - Reglas globales: fixed grounding/no-hallucination + methodology-assignment
 *   rules, previously hardcoded in Python (see `bedrock_settings.global_rules`).
 * Each card saves/resets independently against its own endpoint.
 */
export const AgentPromptsSettingsPage: React.FC = () => {
  const { data, isLoading, isError, error } = useBedrockInstructions()
  const promptUpdate = useBedrockInstructionsUpdate()
  const rulesUpdate = useBedrockGlobalRulesUpdate()

  const [promptDraft, setPromptDraft] = useState('')
  const [rulesDraft, setRulesDraft] = useState('')

  useEffect(() => {
    if (data && promptDraft === '') setPromptDraft(data.system_prompt)
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (data && rulesDraft === '') setRulesDraft(data.global_rules)
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  const promptDirty = data !== undefined && promptDraft !== data.system_prompt
  const rulesDirty = data !== undefined && rulesDraft !== data.global_rules

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Prompts Globales</h1>
        <p className="text-text-secondary mt-2">
          System prompt base y reglas globales que aplican a TODOS los agentes. Los cambios
          aplican desde el siguiente mensaje.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando instrucciones..." />}
      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

      {data && (
        <div className="space-y-6">
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h2 className="text-base font-semibold text-text">System prompt global</h2>
              {data.system_prompt_is_default && (
                <span className="badge badge-cyan">Usando el predeterminado</span>
              )}
            </div>
            <div className="card-body space-y-4">
              <label className="block text-sm font-medium text-text" htmlFor="global-system-prompt">
                Instrucciones base (todos los agentes)
              </label>
              <textarea
                id="global-system-prompt"
                value={promptDraft}
                onChange={(e) => setPromptDraft(e.target.value)}
                rows={16}
                className="input-field text-sm font-mono leading-relaxed resize-y"
              />
              {promptUpdate.isError && (
                <p className="text-red-600 dark:text-red-400 text-xs">{getErrorMessage(promptUpdate.error)}</p>
              )}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                  disabled={!promptDirty || promptUpdate.isPending}
                  onClick={() => promptUpdate.mutate(promptDraft)}
                >
                  <Save size={15} aria-hidden="true" />
                  Guardar
                </button>
                <button
                  type="button"
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-text-secondary hover:bg-glass hover:text-text transition-colors disabled:opacity-50"
                  disabled={data.system_prompt_is_default || promptUpdate.isPending}
                  onClick={() => {
                    promptUpdate.mutate(null)
                    setPromptDraft('')
                  }}
                >
                  <RotateCcw size={15} aria-hidden="true" />
                  Restablecer al predeterminado
                </button>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h2 className="text-base font-semibold text-text">Reglas globales</h2>
              {data.global_rules_is_default && (
                <span className="badge badge-cyan">Usando el predeterminado</span>
              )}
            </div>
            <div className="card-body space-y-4">
              <label className="block text-sm font-medium text-text" htmlFor="global-rules">
                Reglas fijas que aplican a todos los agentes: no alucinar datos, asignación de
                metodologías
              </label>
              <textarea
                id="global-rules"
                value={rulesDraft}
                onChange={(e) => setRulesDraft(e.target.value)}
                rows={16}
                className="input-field text-sm font-mono leading-relaxed resize-y"
              />
              {rulesUpdate.isError && (
                <p className="text-red-600 dark:text-red-400 text-xs">{getErrorMessage(rulesUpdate.error)}</p>
              )}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                  disabled={!rulesDirty || rulesUpdate.isPending}
                  onClick={() => rulesUpdate.mutate(rulesDraft)}
                >
                  <Save size={15} aria-hidden="true" />
                  Guardar
                </button>
                <button
                  type="button"
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-text-secondary hover:bg-glass hover:text-text transition-colors disabled:opacity-50"
                  disabled={data.global_rules_is_default || rulesUpdate.isPending}
                  onClick={() => {
                    rulesUpdate.mutate(null)
                    setRulesDraft('')
                  }}
                >
                  <RotateCcw size={15} aria-hidden="true" />
                  Restablecer al predeterminado
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
