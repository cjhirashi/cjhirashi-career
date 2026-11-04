import React, { useState } from 'react'
import { Target } from 'lucide-react'
import { EmptyState, SectionCard } from '@/components/career/MetricsCharts'
import { useCareerList, useCareerMutations } from '@/hooks/useCareerResource'
import { getErrorMessage } from '@/utils/errors'
import { EVENT_TYPE_OPTIONS, GOAL_TYPES, buildMatch, describeMatch, readMatch, validateMatchInput } from '../configModel'

interface Goal {
  id: string
  name: string
  type: string
  match: Record<string, unknown>
  is_key_event: boolean
}

interface Draft {
  id: string | null
  name: string
  type: string
  value: string
  isKey: boolean
}

const NEW: Draft = { id: null, name: '', type: 'event', value: 'download', isKey: false }

export const GoalsPanel: React.FC<{ siteId: string }> = ({ siteId }) => {
  const { data: goals = [], isLoading } = useCareerList<Goal>('portal-goals', { limit: 100, sortBy: 'created_at', sortDir: 'asc' })
  const { createMutation, updateMutation, deleteMutation } = useCareerMutations<Goal>('portal-goals')
  const [draft, setDraft] = useState<Draft | null>(null)
  const [error, setError] = useState<string | null>(null)

  const type = GOAL_TYPES.find((t) => t.value === draft?.type) ?? GOAL_TYPES[0]
  const busy = createMutation.isPending || updateMutation.isPending

  const edit = (goal: Goal) => {
    setError(null)
    setDraft({ id: goal.id, name: goal.name, type: goal.type, value: readMatch(goal.type, goal.match), isKey: goal.is_key_event })
  }

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft) return
    const problem = !draft.name.trim() ? 'Falta el nombre de la meta.' : validateMatchInput(draft.type, draft.value)
    if (problem) return setError(problem)
    const payload = { name: draft.name.trim(), type: draft.type, match: buildMatch(draft.type, draft.value), is_key_event: draft.isKey }
    try {
      if (draft.id) await updateMutation.mutateAsync({ id: draft.id, payload })
      else await createMutation.mutateAsync({ ...payload, site_id: siteId })
      setDraft(null)
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const remove = async (goal: Goal) => {
    if (!window.confirm(`¿Eliminar la meta «${goal.name}»? Esta acción no se puede deshacer.`)) return
    try {
      await deleteMutation.mutateAsync(goal.id)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <SectionCard title="Metas" subtitle="Qué cuenta como éxito. Una meta clave hace que la visita cuente como comprometida." icon={Target}>
      {isLoading ? (
        <p className="text-text-secondary text-sm">Cargando…</p>
      ) : goals.length === 0 ? (
        <EmptyState message="Aún no hay metas." />
      ) : (
        <ul className="divide-y divide-border mb-4">
          {goals.map((g) => (
            <li key={g.id} className="py-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-text font-medium">
                  {g.name}
                  {g.is_key_event && <span className="ml-2 text-xs text-primary">evento clave</span>}
                </p>
                <p className="text-text-secondary text-xs">{describeMatch(g.type, g.match)}</p>
              </div>
              <div className="flex gap-2">
                <button type="button" className="btn-secondary text-sm" onClick={() => edit(g)} aria-label={`Editar meta ${g.name}`}>Editar</button>
                <button type="button" className="btn-secondary text-sm text-red-600 dark:text-red-400" onClick={() => remove(g)} aria-label={`Eliminar meta ${g.name}`}>Eliminar</button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {draft ? (
        <form onSubmit={save} className="space-y-4 border-t border-border pt-4" aria-label={draft.id ? 'Editar meta' : 'Nueva meta'}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="flex flex-col gap-1 text-sm text-text">
              Nombre
              <input className="input-field" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} maxLength={255} />
            </label>
            <label className="flex flex-col gap-1 text-sm text-text">
              Tipo
              <select
                aria-label="Tipo"
                className="input-field"
                value={draft.type}
                onChange={(e) => setDraft({ ...draft, type: e.target.value, value: e.target.value === 'event' ? 'download' : '' })}
              >
                {GOAL_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm text-text sm:col-span-2">
              {type.inputLabel}
              {type.input === 'event' ? (
                <select aria-label={type.inputLabel} className="input-field" value={draft.value} onChange={(e) => setDraft({ ...draft, value: e.target.value })}>
                  {EVENT_TYPE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              ) : (
                <input className="input-field" value={draft.value} placeholder={type.placeholder} onChange={(e) => setDraft({ ...draft, value: e.target.value })} inputMode={type.input === 'text' ? 'text' : 'decimal'} />
              )}
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-text">
            <input type="checkbox" checked={draft.isKey} onChange={(e) => setDraft({ ...draft, isKey: e.target.checked })} />
            Evento clave (la visita cuenta como comprometida)
          </label>
          {error && <p className="text-red-600 dark:text-red-400 text-sm" role="alert">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" className="btn-primary text-sm" disabled={busy}>{draft.id ? 'Guardar cambios' : 'Crear meta'}</button>
            <button type="button" className="btn-secondary text-sm" onClick={() => { setDraft(null); setError(null) }}>Cancelar</button>
          </div>
        </form>
      ) : (
        <>
          {error && <p className="text-red-600 dark:text-red-400 text-sm mb-3" role="alert">{error}</p>}
          <button type="button" className="btn-primary text-sm" onClick={() => { setError(null); setDraft(NEW) }}>Nueva meta</button>
        </>
      )}
    </SectionCard>
  )
}
