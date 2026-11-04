import React, { useState } from 'react'
import { ArrowDown, ArrowUp, Filter, Trash2 } from 'lucide-react'
import { EmptyState, SectionCard } from '@/components/career/MetricsCharts'
import { useCareerList, useCareerMutations } from '@/hooks/useCareerResource'
import { getErrorMessage } from '@/utils/errors'
import {
  EVENT_TYPE_OPTIONS,
  FUNNEL_STEP_TYPES,
  describeMatch,
  emptyStep,
  moveStep,
  stepsFromApi,
  stepsToPayload,
  validateFunnel,
  type FunnelStepDraft,
  type FunnelStepPayload,
} from '../configModel'

interface Funnel {
  id: string
  name: string
  steps: FunnelStepPayload[]
}

interface Draft {
  id: string | null
  name: string
  steps: FunnelStepDraft[]
}

const newDraft = (): Draft => ({ id: null, name: '', steps: [emptyStep(), emptyStep()] })

export const FunnelsPanel: React.FC<{ siteId: string }> = ({ siteId }) => {
  const { data: funnels = [], isLoading } = useCareerList<Funnel>('portal-funnels', { limit: 100, sortBy: 'created_at', sortDir: 'asc' })
  const { createMutation, updateMutation, deleteMutation } = useCareerMutations<Funnel>('portal-funnels')
  const [draft, setDraft] = useState<Draft | null>(null)
  const [errors, setErrors] = useState<string[]>([])
  const busy = createMutation.isPending || updateMutation.isPending

  const setStep = (index: number, patch: Partial<FunnelStepDraft>) =>
    draft && setDraft({ ...draft, steps: draft.steps.map((s, i) => (i === index ? { ...s, ...patch } : s)) })

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft) return
    const problems = validateFunnel(draft.name, draft.steps)
    if (problems.length > 0) return setErrors(problems)
    const payload = { name: draft.name.trim(), steps: stepsToPayload(draft.steps) }
    try {
      if (draft.id) await updateMutation.mutateAsync({ id: draft.id, payload })
      else await createMutation.mutateAsync({ ...payload, site_id: siteId })
      setDraft(null)
      setErrors([])
    } catch (err) {
      setErrors([getErrorMessage(err)])
    }
  }

  const remove = async (funnel: Funnel) => {
    if (!window.confirm(`¿Eliminar el embudo «${funnel.name}»? Esta acción no se puede deshacer.`)) return
    try {
      await deleteMutation.mutateAsync(funnel.id)
    } catch (err) {
      setErrors([getErrorMessage(err)])
    }
  }

  return (
    <SectionCard title="Embudos" subtitle="Pasos que una visita recorre en orden. Se necesitan al menos 2." icon={Filter}>
      {isLoading ? (
        <p className="text-text-secondary text-sm">Cargando…</p>
      ) : funnels.length === 0 ? (
        <EmptyState message="Aún no hay embudos." />
      ) : (
        <ul className="divide-y divide-border mb-4">
          {funnels.map((f) => (
            <li key={f.id} className="py-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-text font-medium">{f.name}</p>
                <div className="flex gap-2">
                  <button type="button" className="btn-secondary text-sm" aria-label={`Editar embudo ${f.name}`} onClick={() => { setErrors([]); setDraft({ id: f.id, name: f.name, steps: stepsFromApi(f.steps) }) }}>Editar</button>
                  <button type="button" className="btn-secondary text-sm text-red-600 dark:text-red-400" aria-label={`Eliminar embudo ${f.name}`} onClick={() => remove(f)}>Eliminar</button>
                </div>
              </div>
              <ol className="mt-2 text-xs text-text-secondary list-decimal pl-5 space-y-0.5">
                {f.steps.map((s, i) => (
                  <li key={`${s.label}-${i}`}>{s.label} · {describeMatch(s.type, s.match)}</li>
                ))}
              </ol>
            </li>
          ))}
        </ul>
      )}

      {draft ? (
        <form onSubmit={save} className="space-y-4 border-t border-border pt-4" aria-label={draft.id ? 'Editar embudo' : 'Nuevo embudo'}>
          <label className="flex flex-col gap-1 text-sm text-text">
            Nombre
            <input className="input-field" value={draft.name} maxLength={255} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
          </label>

          <ol className="space-y-3">
            {draft.steps.map((step, i) => {
              const spec = FUNNEL_STEP_TYPES.find((t) => t.value === step.type) ?? FUNNEL_STEP_TYPES[0]
              return (
                <li key={i} className="rounded-lg border border-border p-3 space-y-3" aria-label={`Paso ${i + 1}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-text">Paso {i + 1}</span>
                    <div className="flex gap-1">
                      <button type="button" className="p-1 rounded text-text-secondary hover:bg-glass disabled:opacity-30" aria-label={`Subir paso ${i + 1}`} disabled={i === 0} onClick={() => setDraft({ ...draft, steps: moveStep(draft.steps, i, i - 1) })}><ArrowUp size={16} /></button>
                      <button type="button" className="p-1 rounded text-text-secondary hover:bg-glass disabled:opacity-30" aria-label={`Bajar paso ${i + 1}`} disabled={i === draft.steps.length - 1} onClick={() => setDraft({ ...draft, steps: moveStep(draft.steps, i, i + 1) })}><ArrowDown size={16} /></button>
                      <button type="button" className="p-1 rounded text-red-600 dark:text-red-400 hover:bg-glass disabled:opacity-30" aria-label={`Quitar paso ${i + 1}`} disabled={draft.steps.length <= 2} onClick={() => setDraft({ ...draft, steps: draft.steps.filter((_, j) => j !== i) })}><Trash2 size={16} /></button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <label className="flex flex-col gap-1 text-sm text-text">
                      Nombre del paso
                      <input className="input-field" value={step.label} maxLength={255} onChange={(e) => setStep(i, { label: e.target.value })} />
                    </label>
                    <label className="flex flex-col gap-1 text-sm text-text">
                      Tipo
                      <select aria-label="Tipo" className="input-field" value={step.type} onChange={(e) => setStep(i, { type: e.target.value, value: e.target.value === 'event' ? 'download' : '' })}>
                        {FUNNEL_STEP_TYPES.map((t) => (
                          <option key={t.value} value={t.value}>{t.label}</option>
                        ))}
                      </select>
                    </label>
                    <label className="flex flex-col gap-1 text-sm text-text sm:col-span-2">
                      {spec.inputLabel}
                      {spec.input === 'event' ? (
                        <select aria-label={spec.inputLabel} className="input-field" value={step.value} onChange={(e) => setStep(i, { value: e.target.value })}>
                          {EVENT_TYPE_OPTIONS.map((o) => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                          ))}
                        </select>
                      ) : (
                        <input className="input-field" value={step.value} placeholder={spec.placeholder} onChange={(e) => setStep(i, { value: e.target.value })} />
                      )}
                    </label>
                  </div>
                </li>
              )
            })}
          </ol>
          <button type="button" className="btn-secondary text-sm" onClick={() => setDraft({ ...draft, steps: [...draft.steps, emptyStep()] })}>Añadir paso</button>

          {errors.length > 0 && (
            <ul className="text-red-600 dark:text-red-400 text-sm list-disc pl-5" role="alert">
              {errors.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          )}
          <div className="flex gap-2">
            <button type="submit" className="btn-primary text-sm" disabled={busy}>{draft.id ? 'Guardar cambios' : 'Crear embudo'}</button>
            <button type="button" className="btn-secondary text-sm" onClick={() => { setDraft(null); setErrors([]) }}>Cancelar</button>
          </div>
        </form>
      ) : (
        <>
          {errors.length > 0 && <p className="text-red-600 dark:text-red-400 text-sm mb-3" role="alert">{errors[0]}</p>}
          <button type="button" className="btn-primary text-sm" onClick={() => { setErrors([]); setDraft(newDraft()) }}>Nuevo embudo</button>
        </>
      )}
    </SectionCard>
  )
}
