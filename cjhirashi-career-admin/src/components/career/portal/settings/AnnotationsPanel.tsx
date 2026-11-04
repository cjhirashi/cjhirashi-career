import React, { useState } from 'react'
import { StickyNote } from 'lucide-react'
import { EmptyState, SectionCard } from '@/components/career/MetricsCharts'
import { useCareerList, useCareerMutations } from '@/hooks/useCareerResource'
import { getErrorMessage } from '@/utils/errors'
import { ANNOTATION_KINDS } from '../configModel'

interface Annotation {
  id: string
  day: string
  title: string
  kind: string
  ref: string | null
}

interface Draft {
  id: string | null
  day: string
  title: string
  kind: string
  ref: string
}

const NEW: Draft = { id: null, day: '', title: '', kind: 'other', ref: '' }

export const AnnotationsPanel: React.FC<{ siteId: string }> = ({ siteId }) => {
  const { data: items = [], isLoading } = useCareerList<Annotation>('portal-annotations', { limit: 100, sortBy: 'day', sortDir: 'desc' })
  const { createMutation, updateMutation, deleteMutation } = useCareerMutations<Annotation>('portal-annotations')
  const [draft, setDraft] = useState<Draft | null>(null)
  const [error, setError] = useState<string | null>(null)
  const busy = createMutation.isPending || updateMutation.isPending

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft) return
    if (!draft.day) return setError('Falta la fecha.')
    if (!draft.title.trim()) return setError('Falta el título.')
    const payload = { day: draft.day, title: draft.title.trim(), kind: draft.kind, ref: draft.ref.trim() || null }
    try {
      if (draft.id) await updateMutation.mutateAsync({ id: draft.id, payload })
      else await createMutation.mutateAsync({ ...payload, site_id: siteId })
      setDraft(null)
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const remove = async (item: Annotation) => {
    if (!window.confirm(`¿Eliminar la anotación «${item.title}»? Esta acción no se puede deshacer.`)) return
    try {
      await deleteMutation.mutateAsync(item.id)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <SectionCard title="Anotaciones" subtitle="Marcas en la gráfica de visitas: un post, una postulación, un despliegue." icon={StickyNote}>
      {isLoading ? (
        <p className="text-text-secondary text-sm">Cargando…</p>
      ) : items.length === 0 ? (
        <EmptyState message="Aún no hay anotaciones." />
      ) : (
        <ul className="divide-y divide-border mb-4">
          {items.map((a) => (
            <li key={a.id} className="py-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-text font-medium">{a.title}</p>
                <p className="text-text-secondary text-xs">
                  {a.day} · {ANNOTATION_KINDS.find((k) => k.value === a.kind)?.label ?? a.kind}
                  {a.ref ? ` · ${a.ref}` : ''}
                </p>
              </div>
              <div className="flex gap-2">
                <button type="button" className="btn-secondary text-sm" aria-label={`Editar anotación ${a.title}`} onClick={() => { setError(null); setDraft({ id: a.id, day: a.day, title: a.title, kind: a.kind, ref: a.ref ?? '' }) }}>Editar</button>
                <button type="button" className="btn-secondary text-sm text-red-600 dark:text-red-400" aria-label={`Eliminar anotación ${a.title}`} onClick={() => remove(a)}>Eliminar</button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {draft ? (
        <form onSubmit={save} className="space-y-4 border-t border-border pt-4" aria-label={draft.id ? 'Editar anotación' : 'Nueva anotación'}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="flex flex-col gap-1 text-sm text-text">
              Fecha
              <input type="date" className="input-field" value={draft.day} onChange={(e) => setDraft({ ...draft, day: e.target.value })} />
            </label>
            <label className="flex flex-col gap-1 text-sm text-text">
              Tipo
              <select aria-label="Tipo" className="input-field" value={draft.kind} onChange={(e) => setDraft({ ...draft, kind: e.target.value })}>
                {ANNOTATION_KINDS.map((k) => (
                  <option key={k.value} value={k.value}>{k.label}</option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm text-text sm:col-span-2">
              Título
              <input className="input-field" value={draft.title} maxLength={255} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
            </label>
            <label className="flex flex-col gap-1 text-sm text-text sm:col-span-2">
              Referencia (opcional)
              <input className="input-field" value={draft.ref} maxLength={255} placeholder="Enlace o id del post, de la postulación…" onChange={(e) => setDraft({ ...draft, ref: e.target.value })} />
            </label>
          </div>
          {error && <p className="text-red-600 dark:text-red-400 text-sm" role="alert">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" className="btn-primary text-sm" disabled={busy}>{draft.id ? 'Guardar cambios' : 'Crear anotación'}</button>
            <button type="button" className="btn-secondary text-sm" onClick={() => { setDraft(null); setError(null) }}>Cancelar</button>
          </div>
        </form>
      ) : (
        <>
          {error && <p className="text-red-600 dark:text-red-400 text-sm mb-3" role="alert">{error}</p>}
          <button type="button" className="btn-primary text-sm" onClick={() => { setError(null); setDraft(NEW) }}>Nueva anotación</button>
        </>
      )}
    </SectionCard>
  )
}
