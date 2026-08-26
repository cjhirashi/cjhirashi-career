import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Check,
  Pencil,
  RotateCcw,
  Search,
  X,
} from 'lucide-react'
import { useAdminSection, useAdminSections, useAdminSectionUpdate } from '@/hooks/useAdminSections'
import { ThemedSelect } from '@/components/ThemedSelect'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { SectionViewTabs } from '@/components/SectionViewTabs'
import { TableColumnSettings } from '@/components/career/TableColumnSettings'
import { useVisibleTableColumns } from '@/hooks/useVisibleTableColumns'
import { formatCellValue } from '@/components/career/careerFieldUtils'
import { SelectCapsule, SelectCapsuleGroup } from '@/components/SelectCapsule'
import { getErrorMessage } from '@/utils/errors'
import { ColumnConfig, SelectOption } from '@/config/careerResources'
import { ADMIN_SECTION_TYPE_LABEL, AdminSection, AdminSectionView } from '@/types/adminSections'
import { allAgentSelectOptions } from '@/config/agentProfiles'

const agentOptions = [
  { value: '', label: '— Sin agente (orquestador para chat) —' },
  ...allAgentSelectOptions(),
]

const SECTION_TABS = [
  { key: 'list', label: 'Lista' },
  { key: 'view', label: 'Vista' },
  { key: 'edit', label: 'Edición' },
]

const SECTION_COLUMNS: ColumnConfig[] = [
  { key: 'id', label: 'ID' },
  { key: 'label', label: 'Sección' },
  { key: 'section_type', label: 'Tipo' },
  { key: 'agent_label', label: 'Agente' },
  { key: 'view_count', label: 'Vistas', format: 'number' },
  { key: 'path', label: 'Ruta' },
  { key: 'group', label: 'Grupo' },
  { key: 'description', label: 'Descripción', format: 'truncate' },
]

const SECTION_PINNED = ['id', 'label']
const SECTION_DEFAULT_KEYS = SECTION_COLUMNS.map((col) => col.key)

const TYPE_OPTIONS: SelectOption[] = Object.entries(ADMIN_SECTION_TYPE_LABEL).map(([value, label]) => ({
  value,
  label,
}))

type SectionFilters = { section_type: string[]; group: string[] }
const EMPTY_SECTION_FILTERS: SectionFilters = { section_type: [], group: [] }

const compareCells = (a: unknown, b: unknown, dir: 'asc' | 'desc'): number => {
  const av = a == null ? '' : String(a).toLowerCase()
  const bv = b == null ? '' : String(b).toLowerCase()
  const cmp = av.localeCompare(bv, 'es', { numeric: true })
  return dir === 'asc' ? cmp : -cmp
}

export const AdminSectionsPage: React.FC = () => {
  const navigate = useNavigate()
  const { data = [], isLoading, isError, error } = useAdminSections()
  const { columns, selectedKeys, toggleColumn, moveColumn, options, pinnedKeys } = useVisibleTableColumns(
    'admin-sections',
    SECTION_COLUMNS,
    SECTION_DEFAULT_KEYS,
    SECTION_PINNED
  )
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<string | undefined>(undefined)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [filters, setFilters] = useState<SectionFilters>(EMPTY_SECTION_FILTERS)

  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(searchInput.trim().toLowerCase()), 300)
    return () => window.clearTimeout(timer)
  }, [searchInput])

  const groupOptions = useMemo<SelectOption[]>(() => {
    const groups = [...new Set(data.map((row) => row.group).filter(Boolean))].sort()
    return groups.map((value) => ({ value, label: value }))
  }, [data])

  const filtersActive = filters.section_type.length + filters.group.length > 0

  const rows = useMemo(() => {
    let next = data
    if (search) {
      next = next.filter((row) =>
        [row.id, row.label, row.path, row.group, row.agent_label, row.description, row.section_type]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
          .includes(search)
      )
    }
    if (filters.section_type.length) {
      next = next.filter((row) => filters.section_type.includes(row.section_type))
    }
    if (filters.group.length) {
      next = next.filter((row) => filters.group.includes(row.group))
    }
    if (sortBy) {
      next = [...next].sort((a, b) =>
        compareCells(a[sortBy as keyof AdminSection], b[sortBy as keyof AdminSection], sortDir)
      )
    }
    return next
  }, [data, search, filters, sortBy, sortDir])

  const toggleSort = (key: string) => {
    setSortBy((current) => {
      if (current !== key) {
        setSortDir('asc')
        return key
      }
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'))
      return key
    })
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="card has-view-tabs">
        <div className="card-header">
          <h2 className="font-semibold text-text flex items-center gap-2 min-w-0">
            <span className="truncate">Secciones del Admin</span>
            {!isLoading && <span className="badge badge-slate mono">{data.length}</span>}
          </h2>
          <div className="view-tabs-row">
            <SectionViewTabs views={SECTION_TABS} activeKey="list" interactiveKeys={[]} />
          </div>
        </div>
        <div className="card-body">
          {isLoading && <LoadingSpinner fullScreen={false} message="Cargando secciones..." />}
          {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

          {!isLoading && !isError && (
            <>
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <div className="relative flex-1 min-w-[200px]">
                  <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-secondary" />
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Buscar en secciones del admin..."
                    className="input-field pl-8 pr-8 py-1.5 text-sm w-full"
                  />
                  {searchInput && (
                    <button
                      type="button"
                      onClick={() => setSearchInput('')}
                      aria-label="Limpiar búsqueda"
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
                {filtersActive && (
                  <button
                    type="button"
                    className="btn-secondary btn-small"
                    onClick={() => setFilters(EMPTY_SECTION_FILTERS)}
                  >
                    Limpiar filtros
                  </button>
                )}
                <div className="ml-auto flex-shrink-0">
                  <TableColumnSettings
                    options={options}
                    value={selectedKeys}
                    pinnedKeys={pinnedKeys}
                    onToggle={toggleColumn}
                    onMove={moveColumn}
                  />
                </div>
              </div>

              {rows.length === 0 ? (
                <p className="text-text-secondary text-sm text-center py-6">
                  {search || filtersActive
                    ? 'Sin resultados para esa búsqueda o filtros.'
                    : 'No hay secciones.'}
                </p>
              ) : (
                <div className="overflow-x-auto -mx-6">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-text-secondary">
                        {columns.map((col) => (
                          <th
                            key={col.key}
                            className={`px-6 py-2 font-medium whitespace-nowrap${col.key === 'id' ? ' table-col-id' : ''}`}
                          >
                            <span className="inline-flex items-center gap-0.5">
                              <button
                                type="button"
                                onClick={() => toggleSort(col.key)}
                                className={`flex items-center gap-1 ${col.key === 'id' ? 'hover:opacity-80' : 'hover:text-text'}`}
                              >
                                {col.label}
                                {sortBy === col.key ? (
                                  sortDir === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                                ) : (
                                  <ArrowUpDown size={12} className="opacity-30" />
                                )}
                              </button>
                              {col.key === 'section_type' && (
                                <ThemedMultiSelect
                                  variant="icon"
                                  aria-label="Tipo"
                                  value={filters.section_type}
                                  onChange={(section_type) => setFilters((current) => ({ ...current, section_type }))}
                                  options={TYPE_OPTIONS}
                                />
                              )}
                              {col.key === 'group' && groupOptions.length > 0 && (
                                <ThemedMultiSelect
                                  variant="icon"
                                  aria-label="Grupo"
                                  value={filters.group}
                                  onChange={(group) => setFilters((current) => ({ ...current, group }))}
                                  options={groupOptions}
                                />
                              )}
                            </span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((section) => (
                        <tr
                          key={section.id}
                          className="border-b border-border last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer"
                          onClick={() => navigate(`/settings/sections/${section.id}`)}
                        >
                          {columns.map((col) => {
                            if (col.key === 'id') {
                              return (
                                <td key="id" className="px-6 py-2 table-col-id" title={section.id}>
                                  {section.id}
                                </td>
                              )
                            }
                            if (col.key === 'section_type') {
                              return (
                                <td key={col.key} className="px-6 py-2">
                                  <SelectCapsuleGroup>
                                    <SelectCapsule
                                      code={section.section_type}
                                      label={
                                        ADMIN_SECTION_TYPE_LABEL[section.section_type] ?? section.section_type
                                      }
                                    />
                                  </SelectCapsuleGroup>
                                </td>
                              )
                            }
                            if (col.key === 'agent_label') {
                              return (
                                <td key={col.key} className="px-6 py-2">
                                  {section.agent_label ? (
                                    <SelectCapsuleGroup>
                                      <SelectCapsule
                                        code={section.agent_profile_id ?? undefined}
                                        label={section.agent_label}
                                      />
                                      {!section.agent_is_default && (
                                        <SelectCapsule code="override" label="Override" />
                                      )}
                                    </SelectCapsuleGroup>
                                  ) : (
                                    '—'
                                  )}
                                </td>
                              )
                            }
                            return (
                              <td
                                key={col.key}
                                className={`px-6 py-2 text-text${col.format === 'truncate' ? '' : ' whitespace-nowrap'}`}
                              >
                                {formatCellValue(section[col.key as keyof AdminSection], col.format)}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

const Field: React.FC<{ label: string; children: React.ReactNode; wide?: boolean }> = ({
  label,
  children,
  wide,
}) => (
  <div className={wide ? 'md:col-span-2' : ''}>
    <dt className="text-xs text-text-secondary mb-1">{label}</dt>
    <dd className="text-sm text-text">{children}</dd>
  </div>
)

const AdminSectionRecordView: React.FC<{ data: AdminSection }> = ({ data }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">Información</h3>
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="ID">
          <span className="mono text-primary">{data.id}</span>
        </Field>
        <Field label="Tipo">
          <SelectCapsule
            code={data.section_type}
            label={ADMIN_SECTION_TYPE_LABEL[data.section_type] ?? data.section_type}
          />
        </Field>
        <Field label="Ruta">
          <span className="font-mono text-xs">{data.path}</span>
        </Field>
        <Field label="Grupo">{data.group || '—'}</Field>
        <Field label="Agente">
          {data.agent_label ? (
            <SelectCapsule code={data.agent_profile_id ?? undefined} label={data.agent_label} />
          ) : (
            '—'
          )}
        </Field>
        <Field label="Vistas">{data.view_count}</Field>
        <Field label="Descripción" wide>
          {data.description || '—'}
        </Field>
      </dl>
    </div>
    {data.views.map((view) => (
      <div key={view.key}>
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
          Vista: {view.label}
        </h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Clave">
            <span className="font-mono text-xs">{view.key}</span>
          </Field>
          <Field label="Título del sidebar">{view.sidebar_title || '—'}</Field>
          <Field label="Descripción de la vista" wide>
            {view.description || '—'}
          </Field>
          <Field label="Instrucciones del sidebar" wide>
            <p className="whitespace-pre-wrap">{view.sidebar_body || '—'}</p>
          </Field>
        </dl>
      </div>
    ))}
  </div>
)

export const AdminSectionDetailPage: React.FC = () => {
  const navigate = useNavigate()
  const { sectionId = '' } = useParams<{ sectionId: string }>()
  const { data, isLoading, isError, error } = useAdminSection(sectionId)
  const update = useAdminSectionUpdate()
  const [viewState, setViewState] = useState<'view' | 'edit'>('view')
  const [agentId, setAgentId] = useState('')
  const [description, setDescription] = useState('')
  const [views, setViews] = useState<AdminSectionView[]>([])
  const formOpenGuardAt = useRef(0)

  useEffect(() => {
    if (!data) return
    setAgentId(data.agent_profile_id ?? '')
    setDescription(data.description)
    setViews(data.views)
  }, [data])

  const guardFormOpenFromClick = () => {
    formOpenGuardAt.current = performance.now()
  }

  const isGhostFormOpenClick = (event: { isTrusted: boolean }) =>
    event.isTrusted && performance.now() - formOpenGuardAt.current < 400

  const openEdit = () => {
    guardFormOpenFromClick()
    setViewState('edit')
  }

  const cancelForm = () => setViewState('view')

  const save = () => {
    if (!data) return
    update.mutate(
      {
        sectionId: data.id,
        payload: {
          agent_profile_id: agentId,
          description,
          views: Object.fromEntries(
            views.map((view) => [
              view.key,
              {
                description: view.description,
                sidebar_title: view.sidebar_title,
                sidebar_body: view.sidebar_body,
              },
            ])
          ),
        },
      },
      { onSuccess: () => setViewState('view') }
    )
  }

  if (isLoading) {
    return <LoadingSpinner fullScreen={false} message="Cargando sección..." />
  }
  if (isError) {
    return <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
  }
  if (!data) {
    return <p className="text-text-secondary">Sección no encontrada.</p>
  }

  const agentDirty = (agentId || '') !== (data.agent_profile_id ?? '')
  const descriptionDirty = description !== data.description
  const viewsDirty = JSON.stringify(views) !== JSON.stringify(data.views)
  const dirty = agentDirty || descriptionDirty || viewsDirty
  const isSaving = update.isPending

  const headerActions =
    viewState === 'view' ? (
      <button type="button" onClick={openEdit} className="btn-icon btn-icon-sm" aria-label="Editar" title="Editar">
        <Pencil size={13} />
      </button>
    ) : (
      <>
        <button
          type="button"
          onClick={(event) => {
            if (isGhostFormOpenClick(event)) return
            cancelForm()
          }}
          className="btn-icon btn-icon-sm btn-icon-muted"
          aria-label="Cancelar"
          title="Cancelar"
          disabled={isSaving}
        >
          <X size={13} />
        </button>
        <button
          type="button"
          onClick={save}
          className="btn-icon btn-icon-sm"
          aria-label="Actualizar"
          title="Actualizar"
          disabled={!dirty || isSaving}
        >
          <Check size={13} />
        </button>
      </>
    )

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="card has-view-tabs">
        <div className="card-header">
          <h2 className="font-semibold text-text flex items-center gap-2 min-w-0">
            <span className="truncate">Secciones del Admin</span>
            <span className="text-text-muted font-normal">·</span>
            <span className="mono text-primary font-normal flex-shrink-0">{data.id}</span>
            <span className="text-text-muted font-normal">·</span>
            <span className="truncate">{data.label}</span>
          </h2>
          <div className="view-tabs-row">
            <SectionViewTabs
              views={SECTION_TABS}
              activeKey={viewState}
              interactiveKeys={['list']}
              onSelect={(key) => {
                if (key === 'list') navigate('/settings/sections')
              }}
            />
            <div className="view-tabs-actions">{headerActions}</div>
          </div>
        </div>
        <div className="card-body">
          {update.isError && (
            <p className="text-red-600 dark:text-red-400 text-sm mb-4">{getErrorMessage(update.error)}</p>
          )}

          {viewState === 'view' && <AdminSectionRecordView data={data} />}

          {viewState === 'edit' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                  Dominio y descripción
                </h3>
                <div className="space-y-3">
                  <ThemedSelect
                    aria-label="Agente con dominio"
                    value={agentId}
                    onChange={setAgentId}
                    options={agentOptions}
                    placeholder="— Agente —"
                    allowEmpty
                  />
                  <p className="text-xs text-text-muted">
                    Chat contextual: {data.chat_agent_profile_id ?? 'agent_orchestrator'}
                    {data.agent_profile_id && data.chat_agent_profile_id !== data.agent_profile_id
                      ? ' (L3 sin chat; se usa el L2 de respaldo)'
                      : ''}
                  </p>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="input-field text-sm"
                    aria-label="Descripción de la sección"
                  />
                </div>
              </div>

              {views.map((view, index) => (
                <div key={view.key}>
                  <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                    Vista: {view.label}
                    <span className="text-text-muted font-normal text-sm ml-2">({view.key})</span>
                  </h3>
                  <div className="space-y-3">
                    <label className="block text-sm text-text-secondary">
                      Descripción de la vista
                      <textarea
                        value={view.description}
                        onChange={(e) =>
                          setViews((prev) =>
                            prev.map((item, i) =>
                              i === index ? { ...item, description: e.target.value } : item
                            )
                          )
                        }
                        rows={2}
                        className="input-field text-sm mt-1"
                      />
                    </label>
                    <label className="block text-sm text-text-secondary">
                      Título del sidebar
                      <input
                        value={view.sidebar_title}
                        onChange={(e) =>
                          setViews((prev) =>
                            prev.map((item, i) =>
                              i === index ? { ...item, sidebar_title: e.target.value } : item
                            )
                          )
                        }
                        className="input-field text-sm mt-1"
                      />
                    </label>
                    <label className="block text-sm text-text-secondary">
                      Instrucciones del sidebar derecho
                      <textarea
                        value={view.sidebar_body}
                        onChange={(e) =>
                          setViews((prev) =>
                            prev.map((item, i) =>
                              i === index ? { ...item, sidebar_body: e.target.value } : item
                            )
                          )
                        }
                        rows={5}
                        className="input-field text-sm mt-1"
                      />
                    </label>
                  </div>
                </div>
              ))}

              <button
                type="button"
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-text-secondary hover:bg-glass hover:text-text transition-colors disabled:opacity-50"
                disabled={
                  (data.agent_is_default && data.description_is_default && views.every((v) => v.is_default)) ||
                  isSaving
                }
                onClick={() =>
                  update.mutate({
                    sectionId: data.id,
                    payload: { agent_profile_id: '', description: '', views: {} },
                  })
                }
              >
                <RotateCcw size={15} aria-hidden="true" />
                Restablecer al código
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
