import React, { useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight, Pencil, Plus, Trash2 } from 'lucide-react'
import { ResourceConfig } from '@/config/careerResources'
import { useCareerList, useCareerMutations } from '@/hooks/useCareerResource'
import { CareerEntity } from '@/types/career'
import { getErrorMessage } from '@/utils/errors'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Modal } from '@/components/Modal'
import { ResourceForm } from './ResourceForm'
import { formatCellValue } from './careerFieldUtils'

export interface ParentFilter {
  field: string
  value: number
}

interface CareerResourceViewProps {
  config: ResourceConfig
  pageSize?: number
  /** When set, the view fetches up to 100 rows and filters client-side by `field === value` (used for drill-down/nested resources; the backend has no per-field filter query param). */
  parentFilter?: ParentFilter
  /** Fixed values merged into every create/edit payload, hidden from the form (typically the parent FK for a nested resource). */
  presetValues?: Record<string, unknown>
  title?: string
  hideTitle?: boolean
  /** Extra button rendered per row, before Edit/Delete (e.g. "Ver detalle" for drill-down). */
  renderExtraRowAction?: (item: CareerEntity) => React.ReactNode
  /** Extra class applied to a row to highlight the current drill-down selection. */
  rowClassName?: (item: CareerEntity) => string
}

const Badge: React.FC<{ color: 'cyan' | 'slate' | 'success' | 'error' | 'warning'; children: React.ReactNode }> = ({
  color,
  children,
}) => <span className={`badge badge-${color}`}>{children}</span>

const ProjectCard: React.FC<{
  item: CareerEntity
  config: ResourceConfig
  onEdit: () => void
  onDelete: () => void
}> = ({ item, config, onEdit, onDelete }) => {
  const [headingCol, ...restCols] = config.columns
  const summary =
    typeof item.card_summary === 'string'
      ? item.card_summary
      : typeof item.detailed_summary === 'string'
        ? item.detailed_summary
        : null
  const techStack = Array.isArray(item.tech_stack) ? (item.tech_stack as unknown[]) : null

  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-text text-lg">{String(item[headingCol.key] ?? '—')}</h3>
        <div className="flex gap-1 flex-shrink-0">
          <button
            type="button"
            onClick={onEdit}
            aria-label="Editar"
            className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
          >
            <Pencil size={15} />
          </button>
          <button
            type="button"
            onClick={onDelete}
            aria-label="Eliminar"
            className="p-1.5 rounded text-text-secondary hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-600"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {restCols.map((col) => {
          const val = item[col.key]
          if (val === null || val === undefined || val === '') return null
          if (col.format === 'boolean') return val ? (
            <Badge key={col.key} color="cyan">{col.label}</Badge>
          ) : null
          if (col.format === 'badge')
            return (
              <Badge key={col.key} color={col.badgeColor ? col.badgeColor(val) : 'slate'}>
                {String(val)}
              </Badge>
            )
          return (
            <Badge key={col.key} color="slate">
              {col.label}: {formatCellValue(val, col.format)}
            </Badge>
          )
        })}
      </div>

      {summary && <p className="text-text-secondary text-sm line-clamp-3">{summary}</p>}

      {techStack && techStack.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {techStack.slice(0, 8).map((t, idx) => (
            <span
              key={idx}
              className="text-xs px-2 py-0.5 rounded bg-cyan-50 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300"
            >
              {String(t)}
            </span>
          ))}
        </div>
      )}

      {(typeof item.github_url === 'string' || typeof item.demo_url === 'string') && (
        <div className="flex gap-3 text-xs pt-1">
          {typeof item.github_url === 'string' && item.github_url && (
            <a href={item.github_url} target="_blank" rel="noreferrer" className="text-cyan-600 dark:text-cyan-400 hover:underline">
              GitHub
            </a>
          )}
          {typeof item.demo_url === 'string' && item.demo_url && (
            <a href={item.demo_url} target="_blank" rel="noreferrer" className="text-cyan-600 dark:text-cyan-400 hover:underline">
              Demo
            </a>
          )}
        </div>
      )}
    </div>
  )
}

export const CareerResourceView: React.FC<CareerResourceViewProps> = ({
  config,
  pageSize = 20,
  parentFilter,
  presetValues,
  title,
  hideTitle,
  renderExtraRowAction,
  rowClassName,
}) => {
  const isSingleton = config.mode === 'singleton'
  const isNested = !!parentFilter
  const [skip, setSkip] = useState(0)
  const limit = isNested ? 100 : isSingleton ? 1 : pageSize

  const { data, isLoading, isError, error, refetch } = useCareerList<CareerEntity>(config.key, {
    skip: isNested || isSingleton ? 0 : skip,
    limit,
  })
  const { createMutation, updateMutation, deleteMutation } = useCareerMutations<CareerEntity>(config.key)

  const items = useMemo(() => {
    if (!data) return []
    if (isNested && parentFilter) {
      return data.filter((item) => item[parentFilter.field] === parentFilter.value)
    }
    return data
  }, [data, isNested, parentFilter])

  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null)
  const [editingItem, setEditingItem] = useState<CareerEntity | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const closeModal = () => {
    setModalMode(null)
    setEditingItem(null)
    setFormError(null)
  }

  const handleCreate = () => {
    setEditingItem(null)
    setFormError(null)
    setModalMode('create')
  }

  const handleEdit = (item: CareerEntity) => {
    setEditingItem(item)
    setFormError(null)
    setModalMode('edit')
  }

  const handleDelete = (item: CareerEntity) => {
    const demonstrative = config.genderFeminine ? 'esta' : 'este'
    if (
      !window.confirm(`¿Eliminar ${demonstrative} ${config.labelSingular.toLowerCase()}? Esta acción no se puede deshacer.`)
    ) {
      return
    }
    deleteMutation.mutate(item.id)
  }

  const handleSubmit = (payload: Record<string, unknown>) => {
    setFormError(null)
    if (modalMode === 'edit' && editingItem) {
      updateMutation.mutate(
        { id: editingItem.id, payload },
        {
          onSuccess: closeModal,
          onError: (err) => setFormError(getErrorMessage(err)),
        }
      )
    } else {
      createMutation.mutate(payload, {
        onSuccess: closeModal,
        onError: (err) => setFormError(getErrorMessage(err)),
      })
    }
  }

  // ---------------------------------------------------------------------
  // Singleton mode (e.g. `identity`): a single record with an inline form,
  // no table, no pagination, no delete.
  // ---------------------------------------------------------------------
  if (isSingleton) {
    const existing = items[0]
    if (isLoading) return <LoadingSpinner fullScreen={false} message={`Cargando ${config.label.toLowerCase()}...`} />
    return (
      <div className="card">
        {!hideTitle && (
          <div className="card-header">
            <h2 className="font-semibold text-text">{title || config.label}</h2>
          </div>
        )}
        <div className="card-body">
          {isError && (
            <p className="text-red-600 dark:text-red-400 text-sm mb-4">{getErrorMessage(error)}</p>
          )}
          {formError && (
            <p className="text-red-600 dark:text-red-400 text-sm mb-4">{formError}</p>
          )}
          <ResourceForm
            config={config}
            initialValues={existing}
            onSubmit={(payload) => {
              setFormError(null)
              if (existing) {
                updateMutation.mutate(
                  { id: existing.id, payload },
                  { onError: (err) => setFormError(getErrorMessage(err)) }
                )
              } else {
                createMutation.mutate(payload, { onError: (err) => setFormError(getErrorMessage(err)) })
              }
            }}
            isSubmitting={createMutation.isPending || updateMutation.isPending}
            submitLabel={existing ? 'Actualizar' : 'Crear'}
          />
        </div>
      </div>
    )
  }

  const isCards = config.variant === 'cards'

  return (
    <div className={hideTitle ? '' : 'card'}>
      {!hideTitle && (
        <div className="card-header flex items-center justify-between gap-3">
          <h2 className="font-semibold text-text">{title || config.label}</h2>
          <button type="button" onClick={handleCreate} className="btn-primary btn-small flex items-center gap-1">
            <Plus size={14} /> Nuevo
          </button>
        </div>
      )}

      {hideTitle && (
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">
            {title || config.label}
          </h3>
          <button type="button" onClick={handleCreate} className="btn-primary btn-small flex items-center gap-1">
            <Plus size={14} /> Nuevo
          </button>
        </div>
      )}

      <div className={hideTitle ? '' : 'card-body'}>
        {isLoading && <LoadingSpinner fullScreen={false} message="Cargando..." />}

        {isError && (
          <div className="text-center py-6">
            <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
            <button type="button" onClick={() => refetch()} className="btn-secondary btn-small mt-3">
              Reintentar
            </button>
          </div>
        )}

        {!isLoading && !isError && items.length === 0 && (
          <p className="text-text-secondary text-sm text-center py-6">
            No hay {config.label.toLowerCase()} todavía.
          </p>
        )}

        {!isLoading && !isError && items.length > 0 && isCards && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {items.map((item) => (
              <ProjectCard
                key={item.id}
                item={item}
                config={config}
                onEdit={() => handleEdit(item)}
                onDelete={() => handleDelete(item)}
              />
            ))}
          </div>
        )}

        {!isLoading && !isError && items.length > 0 && !isCards && (
          <div className="overflow-x-auto -mx-6">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-text-secondary">
                  {config.columns.map((col) => (
                    <th key={col.key} className="px-6 py-2 font-medium whitespace-nowrap">
                      {col.label}
                    </th>
                  ))}
                  <th className="px-6 py-2 font-medium text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={item.id}
                    className={`border-b border-border last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 ${rowClassName ? rowClassName(item) : ''}`}
                  >
                    {config.columns.map((col) => {
                      const value = item[col.key]
                      if (col.format === 'badge' && value !== null && value !== undefined && value !== '') {
                        return (
                          <td key={col.key} className="px-6 py-2 whitespace-nowrap">
                            <Badge color={col.badgeColor ? col.badgeColor(value) : 'slate'}>
                              {String(value)}
                            </Badge>
                          </td>
                        )
                      }
                      return (
                        <td key={col.key} className="px-6 py-2 whitespace-nowrap text-text">
                          {formatCellValue(value, col.format)}
                        </td>
                      )
                    })}
                    <td className="px-6 py-2 text-right whitespace-nowrap">
                      <div className="flex justify-end items-center gap-1">
                        {renderExtraRowAction?.(item)}
                        <button
                          type="button"
                          onClick={() => handleEdit(item)}
                          aria-label="Editar"
                          className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
                        >
                          <Pencil size={15} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(item)}
                          aria-label="Eliminar"
                          className="p-1.5 rounded text-text-secondary hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-600"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!isNested && !isLoading && !isError && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <button
              type="button"
              onClick={() => setSkip((s) => Math.max(0, s - pageSize))}
              disabled={skip === 0}
              className="btn-secondary btn-small flex items-center gap-1 disabled:opacity-40"
            >
              <ChevronLeft size={14} /> Anterior
            </button>
            <span className="text-xs text-text-secondary">
              Mostrando {items.length === 0 ? 0 : skip + 1}–{skip + items.length}
            </span>
            <button
              type="button"
              onClick={() => setSkip((s) => s + pageSize)}
              disabled={items.length < pageSize}
              className="btn-secondary btn-small flex items-center gap-1 disabled:opacity-40"
            >
              Siguiente <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>

      {modalMode && (
        <Modal
          title={
            modalMode === 'create'
              ? `${config.genderFeminine ? 'Nueva' : 'Nuevo'} ${config.labelSingular}`
              : `Editar ${config.labelSingular}`
          }
          onClose={closeModal}
        >
          {formError && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg">
              <p className="text-red-800 dark:text-red-300 text-sm font-medium">{formError}</p>
            </div>
          )}
          <ResourceForm
            config={config}
            initialValues={editingItem || undefined}
            presetValues={presetValues}
            onSubmit={handleSubmit}
            onCancel={closeModal}
            isSubmitting={createMutation.isPending || updateMutation.isPending}
            submitLabel={modalMode === 'create' ? 'Crear' : 'Actualizar'}
          />
        </Modal>
      )}
    </div>
  )
}
