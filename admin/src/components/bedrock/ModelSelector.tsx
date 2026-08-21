import React, { useState } from 'react'
import { Check, ChevronDown, Cpu, RotateCw } from 'lucide-react'
import { useBedrockModel, useBedrockModelSwitch } from '@/hooks/useBedrockChat'
import { getErrorMessage } from '@/utils/errors'

/** Dropdown limited to `settings.BEDROCK_AVAILABLE_MODELS` (see
 * api/src/config.py) - every option here already has its IAM access (and,
 * for Anthropic models, its AWS Marketplace agreement) provisioned on the
 * harness execution role, so picking one is always safe. Switching models
 * is a control-plane call on AWS's side (`UpdateHarness`) - it can take a
 * few seconds, hence the pending state.
 *
 * A custom button+popover instead of a native <select>: a native <option>
 * list is rendered by the OS/browser, not by our CSS, so it always shows up
 * with a plain white background regardless of the app's dark theme - this
 * matches the popover styling `Navbar.tsx`'s user menu already uses. */
export const ModelSelector: React.FC = () => {
  const { data, isLoading, isError, error, refetch } = useBedrockModel()
  const switchModel = useBedrockModelSwitch()
  const [open, setOpen] = useState(false)

  if (isError) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400" title={getErrorMessage(error)}>
        <Cpu size={13} aria-hidden="true" />
        <span>No se pudo cargar el modelo</span>
        <button
          type="button"
          onClick={() => refetch()}
          aria-label="Reintentar"
          title="Reintentar"
          className="hover:text-text transition-colors"
        >
          <RotateCw size={12} aria-hidden="true" />
        </button>
      </div>
    )
  }

  if (isLoading || !data || !Array.isArray(data.available_models)) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-text-secondary">
        <Cpu size={13} aria-hidden="true" />
        <span>Cargando modelo...</span>
      </div>
    )
  }

  const current = data.available_models.find((m) => m.model_id === data.current_model_id)

  const pick = (modelId: string) => {
    setOpen(false)
    if (modelId !== data.current_model_id) switchModel.mutate(modelId)
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={switchModel.isPending}
        aria-haspopup="true"
        aria-expanded={open}
        title={
          current
            ? `$${current.price_input_per_million}/M entrada · $${current.price_output_per_million}/M salida`
            : undefined
        }
        className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text transition-colors disabled:opacity-50"
      >
        <Cpu size={13} className="flex-shrink-0" aria-hidden="true" />
        <span>{switchModel.isPending ? 'Cambiando...' : current?.label ?? data.current_model_id}</span>
        <ChevronDown size={12} className="flex-shrink-0" aria-hidden="true" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div
            className="absolute left-0 mt-2 w-56 z-50 rounded-2xl border shadow-glass overflow-hidden"
            style={{ backgroundColor: 'var(--bg-popover)', borderColor: 'var(--border-glass)', backdropFilter: 'blur(16px)' }}
          >
            {data.available_models.map((model) => (
              <button
                key={model.model_id}
                type="button"
                onClick={() => pick(model.model_id)}
                className="w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-text hover:bg-glass transition-colors text-left"
              >
                <span>
                  {model.label}
                  <span className="block text-[11px] text-text-secondary">
                    ${model.price_input_per_million}/M · ${model.price_output_per_million}/M
                  </span>
                </span>
                {model.model_id === data.current_model_id && (
                  <Check size={14} className="text-primary flex-shrink-0" aria-hidden="true" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
