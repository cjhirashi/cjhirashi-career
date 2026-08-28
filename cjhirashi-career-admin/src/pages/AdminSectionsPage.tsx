import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Check, Pencil, RotateCcw, X } from 'lucide-react'
import { useAdminSection, useAdminSections, useAdminSectionUpdate } from '@/hooks/useAdminSections'
import { ThemedSelect } from '@/components/ThemedSelect'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { SelectCapsule, SelectCapsuleGroup } from '@/components/SelectCapsule'
import { getErrorMessage } from '@/utils/errors'
import { ColumnConfig, SelectOption } from '@/config/careerResources'
import { ADMIN_SECTION_TYPE_LABEL, AdminSection, AdminSectionView } from '@/types/adminSections'
import { allAgentSelectOptions } from '@/config/agentProfiles'
import {
  DetailSectionTemplate,
  SectionRecordView,
  TableSectionTemplate,
  useSectionTable,
} from '@/components/section'

const SECTION_TITLE = 'Secciones del Admin'
const LIST_PATH = '/settings/sections'

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
  { key: 'system_name', label: 'Nombre de sistema' },
  { key: 'label', label: 'Sección' },
  { key: 'section_type', label: 'Tipo' },
  { key: 'agent_label', label: 'Agente' },
  { key: 'view_count', label: 'Vistas', format: 'number' },
  { key: 'path', label: 'Ruta' },
  { key: 'group', label: 'Grupo' },
  { key: 'description', label: 'Descripción', format: 'truncate' },
]

const TYPE_OPTIONS: SelectOption[] = Object.entries(ADMIN_SECTION_TYPE_LABEL).map(([value, label]) => ({
  value,
  label,
}))

type SectionFilters = { section_type: string[]; group: string[] }
const EMPTY_SECTION_FILTERS: SectionFilters = { section_type: [], group: [] }

// ===========================================================================
// Lista
// ===========================================================================

export const AdminSectionsPage: React.FC = () => {
  const navigate = useNavigate()
  const { data = [], isLoading, isError, error } = useAdminSections()
  const [filters, setFilters] = useState<SectionFilters>(EMPTY_SECTION_FILTERS)

  const groupOptions = useMemo<SelectOption[]>(() => {
    const groups = [...new Set(data.map((row) => row.group).filter(Boolean))].sort()
    return groups.map((value) => ({ value, label: value }))
  }, [data])

  const filteredData = useMemo(() => {
    let next = data
    if (filters.section_type.length) {
      next = next.filter((row) => filters.section_type.includes(row.section_type))
    }
    if (filters.group.length) {
      next = next.filter((row) => filters.group.includes(row.group))
    }
    return next
  }, [data, filters])

  const { visibleColumns, columnSettings, sort, toggleSort, searchInput, setSearchInput, rows } =
    useSectionTable<AdminSection>({
      storageKey: 'admin-sections',
      columns: SECTION_COLUMNS,
      pinnedKeys: ['id', 'label'],
      rows: filteredData,
      searchAccessor: (row) =>
        [
          row.id,
          row.system_name,
          row.label,
          row.path,
          row.group,
          row.agent_label,
          row.description,
          row.section_type,
        ]
          .filter(Boolean)
          .join(' '),
    })

  const filtersActive = filters.section_type.length + filters.group.length > 0

  const renderCell = (row: AdminSection, key: string): React.ReactNode | undefined => {
    if (key === 'section_type') {
      return (
        <SelectCapsuleGroup>
          <SelectCapsule
            code={row.section_type}
            label={ADMIN_SECTION_TYPE_LABEL[row.section_type] ?? row.section_type}
          />
        </SelectCapsuleGroup>
      )
    }
    if (key === 'agent_label') {
      return row.agent_label ? (
        <SelectCapsuleGroup>
          <SelectCapsule code={row.agent_profile_id ?? undefined} label={row.agent_label} />
          {!row.agent_is_default && <SelectCapsule code="override" label="Override" />}
        </SelectCapsuleGroup>
      ) : (
        '—'
      )
    }
    return undefined
  }

  const headerExtra = (key: string): React.ReactNode => {
    if (key === 'section_type') {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Tipo"
          value={filters.section_type}
          onChange={(section_type) => setFilters((c) => ({ ...c, section_type }))}
          options={TYPE_OPTIONS}
        />
      )
    }
    if (key === 'group' && groupOptions.length > 0) {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Grupo"
          value={filters.group}
          onChange={(group) => setFilters((c) => ({ ...c, group }))}
          options={groupOptions}
        />
      )
    }
    return null
  }

  return (
    <TableSectionTemplate<AdminSection>
      title={SECTION_TITLE}
      count={isLoading ? undefined : data.length}
      query={{ isLoading, isError, error }}
      toolbar={{
        search: {
          value: searchInput,
          onChange: setSearchInput,
          placeholder: 'Buscar en secciones del admin...',
        },
        filtersActive,
        onClearFilters: () => setFilters(EMPTY_SECTION_FILTERS),
        columnSettings,
      }}
      table={{
        columns: visibleColumns,
        rows,
        getRowKey: (r) => r.id,
        sort,
        onToggleSort: toggleSort,
        onRowClick: (r) => navigate(`${LIST_PATH}/${r.id}`),
        renderCell,
        headerExtra,
        emptyMessage: filtersActive
          ? 'Sin resultados para esa búsqueda o filtros.'
          : 'No hay secciones.',
      }}
      footer={{ variant: 'count', total: data.length }}
    />
  )
}

// ===========================================================================
// Detalle
// ===========================================================================

const recordGroups = (data: AdminSection) => [
  {
    title: 'Información',
    fields: [
      { label: 'ID', value: <span className="mono text-primary">{data.id}</span> },
      {
        label: 'Nombre de sistema',
        value: <span className="mono text-primary">{data.system_name}</span>,
      },
      {
        label: 'Tipo',
        value: (
          <SelectCapsule
            code={data.section_type}
            label={ADMIN_SECTION_TYPE_LABEL[data.section_type] ?? data.section_type}
          />
        ),
      },
      { label: 'Ruta', value: <span className="font-mono text-xs">{data.path}</span> },
      { label: 'Grupo', value: data.group || '—' },
      {
        label: 'Agente',
        value: data.agent_label ? (
          <SelectCapsule code={data.agent_profile_id ?? undefined} label={data.agent_label} />
        ) : (
          '—'
        ),
      },
      { label: 'Vistas', value: data.view_count },
      { label: 'Descripción', wide: true, value: data.description || '—' },
    ],
  },
  ...data.views.map((view) => ({
    title: `Vista: ${view.label}`,
    fields: [
      { label: 'Clave', value: <span className="font-mono text-xs">{view.key}</span> },
      { label: 'Título del sidebar', value: view.sidebar_title || '—' },
      { label: 'Descripción de la vista', wide: true, value: view.description || '—' },
      {
        label: 'Instrucciones del sidebar',
        wide: true,
        value: <p className="whitespace-pre-wrap">{view.sidebar_body || '—'}</p>,
      },
    ],
  })),
]

export const AdminSectionDetailPage: React.FC = () => {
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

  useEffect(() => {
    setViewState('view')
  }, [sectionId])

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
            ]),
          ),
        },
      },
      { onSuccess: () => setViewState('view') },
    )
  }

  if (isLoading) return <LoadingSpinner fullScreen={false} message="Cargando sección..." />
  if (isError) return <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
  if (!data) return <p className="text-text-secondary">Sección no encontrada.</p>

  const agentDirty = (agentId || '') !== (data.agent_profile_id ?? '')
  const descriptionDirty = description !== data.description
  const viewsDirty = JSON.stringify(views) !== JSON.stringify(data.views)
  const dirty = agentDirty || descriptionDirty || viewsDirty
  const isSaving = update.isPending

  const actions =
    viewState === 'view' ? (
      <button
        type="button"
        onClick={openEdit}
        className="btn-icon btn-icon-sm"
        aria-label="Editar"
        title="Editar"
      >
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
    <DetailSectionTemplate
      sectionTitle={SECTION_TITLE}
      listPath={LIST_PATH}
      record={{ id: data.id, name: data.label }}
      tabs={SECTION_TABS}
      activeTab={viewState}
      interactiveTabs={['list']}
      actions={actions}
    >
      {update.isError && (
        <p className="text-red-600 dark:text-red-400 text-sm mb-4">{getErrorMessage(update.error)}</p>
      )}

      {viewState === 'view' && <SectionRecordView groups={recordGroups(data)} />}

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
                          i === index ? { ...item, description: e.target.value } : item,
                        ),
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
                          i === index ? { ...item, sidebar_title: e.target.value } : item,
                        ),
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
                          i === index ? { ...item, sidebar_body: e.target.value } : item,
                        ),
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
    </DetailSectionTemplate>
  )
}
