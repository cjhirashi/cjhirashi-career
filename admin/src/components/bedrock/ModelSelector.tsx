import React from 'react'
import { Cpu } from 'lucide-react'
import { useBedrockModel, useBedrockModelSwitch } from '@/hooks/useBedrockChat'

/** Dropdown limited to `settings.BEDROCK_AVAILABLE_MODELS` (see
 * api/src/config.py) - every option here already has its IAM access (and,
 * for Anthropic models, its AWS Marketplace agreement) provisioned on the
 * harness execution role, so picking one is always safe. Switching models
 * is a control-plane call on AWS's side (`UpdateHarness`) - it can take a
 * few seconds, hence the pending state. */
export const ModelSelector: React.FC = () => {
  const { data, isLoading } = useBedrockModel()
  const switchModel = useBedrockModelSwitch()

  if (isLoading || !data) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
        <Cpu size={13} aria-hidden="true" />
        <span>Cargando modelo...</span>
      </div>
    )
  }

  const current = data.available_models.find((m) => m.model_id === data.current_model_id)

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <Cpu size={13} className="text-text-secondary flex-shrink-0" aria-hidden="true" />
      <select
        value={data.current_model_id}
        disabled={switchModel.isPending}
        onChange={(e) => switchModel.mutate(e.target.value)}
        aria-label="Modelo del asistente"
        title={
          current
            ? `$${current.price_input_per_million}/M entrada · $${current.price_output_per_million}/M salida`
            : undefined
        }
        className="bg-transparent text-text-secondary hover:text-text border-none focus:outline-none cursor-pointer disabled:opacity-50 text-xs"
      >
        {data.available_models.map((model) => (
          <option key={model.model_id} value={model.model_id}>
            {model.label}
          </option>
        ))}
      </select>
      {switchModel.isPending && <span className="text-text-muted">cambiando...</span>}
    </div>
  )
}
