import React, { useEffect, useState } from 'react'
import { RotateCcw, Save } from 'lucide-react'
import {
  useBedrockAgentProfilePrompts,
  useBedrockAgentProfilePromptUpdate,
} from '@/hooks/useBedrockChat'
import { AGENT_PROFILES } from '@/config/agentProfiles'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

export const AgentInstructionsPage: React.FC = () => {
  const {
    data: profiles = [],
    isLoading: profilesLoading,
    isError: profilesError,
    error: profilesLoadError,
  } = useBedrockAgentProfilePrompts()
  const profileUpdate = useBedrockAgentProfilePromptUpdate()
  const [selectedProfileId, setSelectedProfileId] = useState<string>('agent_orchestrator')
  const [profileDraft, setProfileDraft] = useState('')

  const selectedProfile = profiles.find((p) => p.profile_id === selectedProfileId)

  useEffect(() => {
    if (selectedProfile) {
      setProfileDraft(selectedProfile.effective_suffix)
    }
  }, [selectedProfileId, selectedProfile?.effective_suffix, selectedProfile?.is_default])

  const profileDirty =
    selectedProfile !== undefined && profileDraft !== selectedProfile.effective_suffix

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Instrucciones por Especialista</h1>
        <p className="text-text-secondary mt-2">
          Suffix por especialista (L1 orquestador, L2 área, L3 tarea), sumado al prompt base
          global (ver Settings → Prompts Globales). Los agentes L3 no tienen chat; igual puedes
          editar su suffix. Los cambios aplican desde el siguiente mensaje.
        </p>
      </div>

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
                <span className="ml-2 text-[10px] text-text-muted">L{p.level ?? 2}</span>
                {!p.user_facing && (
                  <span className="block text-[10px] text-text-muted">Sin chat (tarea)</span>
                )}
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
    </div>
  )
}

function getProfileLabel(profileId: string): string {
  return AGENT_PROFILES.find((p) => p.id === profileId)?.label ?? profileId
}
