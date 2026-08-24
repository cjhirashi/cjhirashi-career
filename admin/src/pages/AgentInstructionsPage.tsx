import React, { useEffect, useState } from 'react'
import { RotateCcw, Save } from 'lucide-react'
import {
  useBedrockAgentProfilePrompts,
  useBedrockAgentProfilePromptUpdate,
  useBedrockInstructions,
  useBedrockInstructionsUpdate,
} from '@/hooks/useBedrockChat'
import { AGENT_PROFILES } from '@/config/agentProfiles'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

type InstructionsTab = 'global' | 'profiles'

export const AgentInstructionsPage: React.FC = () => {
  const [tab, setTab] = useState<InstructionsTab>('global')
  const { data, isLoading, isError, error } = useBedrockInstructions()
  const update = useBedrockInstructionsUpdate()
  const [draft, setDraft] = useState('')

  const {
    data: profiles = [],
    isLoading: profilesLoading,
    isError: profilesError,
    error: profilesLoadError,
  } = useBedrockAgentProfilePrompts()
  const profileUpdate = useBedrockAgentProfilePromptUpdate()
  const [selectedProfileId, setSelectedProfileId] = useState<string>('orchestrator')
  const [profileDraft, setProfileDraft] = useState('')

  useEffect(() => {
    if (data && draft === '') setDraft(data.system_prompt)
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectedProfile = profiles.find((p) => p.profile_id === selectedProfileId)

  useEffect(() => {
    if (selectedProfile) {
      setProfileDraft(selectedProfile.effective_suffix)
    }
  }, [selectedProfileId, selectedProfile?.effective_suffix, selectedProfile?.is_default])

  const isDirty = data !== undefined && draft !== data.system_prompt
  const profileDirty =
    selectedProfile !== undefined && profileDraft !== selectedProfile.effective_suffix

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Instrucciones del Agente</h1>
        <p className="text-text-secondary mt-2">
          Prompt base global y suffix por especialista. Puedes referenciar metodologías (p. ej. «consulta
          search_knowledge_base en la sección Diseño PDF»). Los cambios aplican desde el siguiente mensaje.
        </p>
      </div>

      <div
        className="tab-pill mb-6"
        role="tablist"
        aria-label="Tipo de instrucciones"
      >
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'global'}
          onClick={() => setTab('global')}
          className="tab-pill-btn"
        >
          Prompt global
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'profiles'}
          onClick={() => setTab('profiles')}
          className="tab-pill-btn"
        >
          Por especialista
        </button>
        <span className="tab-pill-indicator" data-pos={tab === 'global' ? '0' : '1'} aria-hidden="true" />
      </div>

      {tab === 'global' && (
        <>
          {isLoading && <LoadingSpinner fullScreen={false} message="Cargando instrucciones..." />}
          {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

          {data && (
            <div className="card">
              <div className="card-header flex items-center justify-between">
                <h2 className="text-base font-semibold text-text">System prompt global</h2>
                {data.is_default && <span className="badge badge-cyan">Usando el predeterminado</span>}
              </div>
              <div className="card-body space-y-4">
                <label className="block text-sm font-medium text-text" htmlFor="global-system-prompt">
                  Instrucciones base (todos los agentes)
                </label>
                <textarea
                  id="global-system-prompt"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={16}
                  className="input-field text-sm font-mono leading-relaxed resize-y"
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
        </>
      )}

      {tab === 'profiles' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="card lg:col-span-1">
            <div className="card-header">
              <h2 className="text-base font-semibold text-text">Especialistas</h2>
            </div>
            <div className="card-body space-y-1">
              {profilesLoading && <LoadingSpinner fullScreen={false} message="Cargando perfiles..." />}
              {profilesError && (
                <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(profilesLoadError)}</p>
              )}
              {profiles.map((p) => (
                <button
                  key={p.profile_id}
                  type="button"
                  onClick={() => setSelectedProfileId(p.profile_id)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-sm transition-colors ${
                    selectedProfileId === p.profile_id
                      ? 'bg-primary/15 text-text'
                      : 'hover:bg-glass text-text-secondary'
                  }`}
                >
                  <span className="font-medium text-text">{p.label}</span>
                  {!p.is_default && (
                    <span className="block text-[10px] text-primary">Personalizado</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="card lg:col-span-2">
            <div className="card-header flex items-center justify-between gap-2">
              <h2 className="text-base font-semibold text-text">
                {selectedProfile?.label ?? getProfileLabel(selectedProfileId)}
              </h2>
              {selectedProfile && !selectedProfile.is_default && (
                <span className="badge badge-cyan">Override activo</span>
              )}
            </div>
            <div className="card-body space-y-4">
              {selectedProfile && (
                <details className="text-xs text-text-muted">
                  <summary className="cursor-pointer hover:text-text-secondary">Ver predeterminado en código</summary>
                  <pre className="mt-2 p-3 rounded-xl bg-glass whitespace-pre-wrap font-mono text-[11px]">
                    {selectedProfile.default_suffix}
                  </pre>
                </details>
              )}
              <label className="block text-sm font-medium text-text" htmlFor="profile-system-prompt">
                Instrucciones del especialista
              </label>
              <textarea
                id="profile-system-prompt"
                value={profileDraft}
                onChange={(e) => setProfileDraft(e.target.value)}
                rows={14}
                className="input-field text-sm font-mono leading-relaxed resize-y"
                placeholder="Instrucciones específicas: metodologías, tono, herramientas…"
              />
              {profileUpdate.isError && (
                <p className="text-red-600 dark:text-red-400 text-xs">{getErrorMessage(profileUpdate.error)}</p>
              )}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                  disabled={!profileDirty || profileUpdate.isPending || !selectedProfile}
                  onClick={() =>
                    profileUpdate.mutate({
                      profileId: selectedProfileId,
                      systemPromptSuffix: profileDraft,
                    })
                  }
                >
                  <Save size={15} aria-hidden="true" />
                  Guardar
                </button>
                <button
                  type="button"
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-text-secondary hover:bg-glass hover:text-text transition-colors disabled:opacity-50"
                  disabled={selectedProfile?.is_default || profileUpdate.isPending}
                  onClick={() => {
                    profileUpdate.mutate({ profileId: selectedProfileId, systemPromptSuffix: null })
                    if (selectedProfile) setProfileDraft(selectedProfile.default_suffix)
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

function getProfileLabel(profileId: string): string {
  return AGENT_PROFILES.find((p) => p.id === profileId)?.label ?? profileId
}
