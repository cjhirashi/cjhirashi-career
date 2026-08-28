import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Check, Pencil, RotateCcw, X } from 'lucide-react'
import { useAdminView, useAdminViewUpdate, useAdminViews } from '@/hooks/useAdminViews'
import { ThemedSelect } from '@/components/ThemedSelect'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { SelectCapsule, SelectCapsuleGroup } from '@/components/SelectCapsule'
import { getErrorMessage } from '@/utils/errors'
import { ColumnConfig, SelectOption } from '@/config/careerResources'
import { ADMIN_DATA_SOURCE_LABEL, AdminViewItem } from '@/types/adminSections'
import { l2AgentSelectOptions } from '@/config/agentProfiles'
import {
  DetailSectionTemplate,
  SectionRecordView,
  TableSectionTemplate,
  useSectionTable,
} from '@/components/section'

const SECTION_TITLE = 'Vistas'
const LIST_PATH = '/settings/views'

const agentOptions = [{ value: '', label: '— Sin agente (chat deshabilitado) —' }, ...l2AgentSelectOptions()]

const VIEW_COLUMNS: ColumnConfig[] = [
  { key: 'id', label: 'ID' },
  { key: 'label', label: 'Vista' },
  { key: 'section_label', label: 'Sección' },
  { key: 'data_source', label: 'Origen' },
  { key: 'responsible_agent_label', label: 'Responsable' },
  { key: 'chat_enabled', label: 'Chat', format: 'boolean' },
  { key: 'instructions_enabled', label: 'Instrucciones', format: 'boolean' },
]

const DATA_SOURCE_OPTIONS: SelectOption[] = Object.entries(ADMIN_DATA_SOURCE_LABEL).map(
  ([value, label]) => ({ value, label })
)

interface ViewRow extends AdminViewItem {
  section_label: string
}

// ===========================================================================
// Lista
// ===========================================================================

export const AdminViewsPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sectionIdParam = searchParams.get('section_id') ?? undefined
  const { data = [], isLoading, isError, error } = useAdminViews(
    sectionIdParam ? { section_id: sectionIdParam } : undefined
  )
  const [dataSourceFilter, setDataSourceFilter] = useState<string[]>([])

  const rows: ViewRow[] = useMemo(
    () => data.map((item) => ({ ...item, section_label: item.owner.section_label })),
    [data]
  )

  const filteredData = useMemo(() => {
    if (!dataSourceFilter.length) return rows
    return rows.filter((row) => dataSourceFilter.includes(row.data_source))
  }, [rows, dataSourceFilter])

  const { visibleColumns, columnSettings, sort, toggleSort, searchInput, setSearchInput, rows: tableRows } =
    useSectionTable<ViewRow>({
      storageKey: 'admin-views',
      columns: VIEW_COLUMNS,
      pinnedKeys: ['id', 'label'],
      rows: filteredData,
      searchAccessor: (row) =>
        [row.id, row.label, row.key, row.section_label, row.responsible_agent_label]
          .filter(Boolean)
          .join(' '),
    })

  const filtersActive = dataSourceFilter.length > 0

  const renderCell = (row: ViewRow, key: string): React.ReactNode | undefined => {
    if (key === 'data_source') {
      return (
        <SelectCapsuleGroup>
          <SelectCapsule code={row.data_source} label={ADMIN_DATA_SOURCE_LABEL[row.data_source] ?? row.data_source} />
        </SelectCapsuleGroup>
      )
    }
    if (key === 'responsible_agent_label') {
      return row.responsible_agent_label ? (
        <SelectCapsule code={row.responsible_agent_profile_id ?? undefined} label={row.responsible_agent_label} />
      ) : (
        '—'
      )
    }
    return undefined
  }

  const headerExtra = (key: string): React.ReactNode => {
    if (key === 'data_source') {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Origen de datos"
          value={dataSourceFilter}
          onChange={setDataSourceFilter}
          options={DATA_SOURCE_OPTIONS}
        />
      )
    }
    return null
  }

  return (
    <TableSectionTemplate<ViewRow>
      title={SECTION_TITLE}
      count={isLoading ? undefined : rows.length}
      query={{ isLoading, isError, error }}
      toolbar={{
        search: {
          value: searchInput,
          onChange: setSearchInput,
          placeholder: 'Buscar en vistas...',
        },
        filtersActive,
        onClearFilters: () => setDataSourceFilter([]),
        columnSettings,
      }}
      table={{
        columns: visibleColumns,
        rows: tableRows,
        getRowKey: (r) => r.id,
        sort,
        onToggleSort: toggleSort,
        onRowClick: (r) => navigate(`${LIST_PATH}/${r.id}`),
        renderCell,
        headerExtra,
        emptyMessage: filtersActive
          ? 'Sin resultados para esa búsqueda o filtros.'
          : sectionIdParam
            ? 'Esta sección no tiene vistas.'
            : 'No hay vistas.',
      }}
      footer={{ variant: 'count', total: rows.length }}
    />
  )
}

// ===========================================================================
// Detalle
// ===========================================================================

const recordGroups = (data: AdminViewItem) => [
  {
    title: 'Información',
    fields: [
      { label: 'ID', value: <span className="mono text-primary">{data.id}</span> },
      { label: 'Clave', value: <span className="mono text-xs">{data.key}</span> },
      { label: 'Etiqueta', value: data.label },
      {
        label: 'Sección',
        value: (
          <span>
            {data.owner.section_label}{' '}
            <span className="mono text-xs text-text-muted">({data.owner.section_id})</span>
          </span>
        ),
      },
      {
        label: 'Origen de datos',
        value: (
          <SelectCapsule
            code={data.data_source}
            label={ADMIN_DATA_SOURCE_LABEL[data.data_source] ?? data.data_source}
          />
        ),
      },
      { label: 'Recurso', value: data.resource_key || '—' },
      { label: 'Orden', value: data.sort_order },
      { label: 'Ventana de controles', value: data.has_controls_window ? 'Sí' : 'No' },
      { label: 'Tools', wide: true, value: data.tool_names.length ? data.tool_names.join(', ') : '—' },
    ],
  },
  {
    title: 'Configuración del operador',
    fields: [
      {
        label: 'Agente responsable',
        value: data.responsible_agent_label ? (
          <SelectCapsule code={data.responsible_agent_profile_id ?? undefined} label={data.responsible_agent_label} />
        ) : (
          '— Sin agente (chat deshabilitado) —'
        ),
      },
      { label: 'Chat contextual', value: data.chat_enabled ? 'Habilitado' : 'Deshabilitado' },
      { label: 'Panel de instrucciones', value: data.instructions_enabled ? 'Habilitado' : 'Deshabilitado' },
      {
        label: 'Instrucciones',
        wide: true,
        value: <p className="whitespace-pre-wrap">{data.instructions || '—'}</p>,
      },
    ],
  },
]

export const AdminViewDetailPage: React.FC = () => {
  const { viewId = '' } = useParams<{ viewId: string }>()
  const { data, isLoading, isError, error } = useAdminView(viewId)
  const update = useAdminViewUpdate()
  const [viewState, setViewState] = useState<'view' | 'edit'>('view')
  const [agentId, setAgentId] = useState('')
  const [instructions, setInstructions] = useState('')

  useEffect(() => {
    if (!data) return
    setAgentId(data.responsible_agent_profile_id ?? '')
    setInstructions(data.instructions ?? '')
  }, [data])

  useEffect(() => {
    setViewState('view')
  }, [viewId])

  const openEdit = () => setViewState('edit')
  const cancelForm = () => setViewState('view')

  const save = () => {
    if (!data) return
    update.mutate(
      {
        viewId: data.id,
        payload: {
          responsible_agent_profile_id: agentId,
          instructions,
        },
      },
      { onSuccess: () => setViewState('view') }
    )
  }

  const resetToDefault = () => {
    if (!data) return
    update.mutate({ viewId: data.id, payload: { responsible_agent_profile_id: '', instructions: '' } })
  }

  if (isLoading) return <LoadingSpinner fullScreen={false} message="Cargando vista..." />
  if (isError) return <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
  if (!data) return <p className="text-text-secondary">Vista no encontrada.</p>

  const agentDirty = (agentId || '') !== (data.responsible_agent_profile_id ?? '')
  const instructionsDirty = instructions !== (data.instructions ?? '')
  const dirty = agentDirty || instructionsDirty
  const isSaving = update.isPending

  const actions =
    viewState === 'view' ? (
      <button type="button" onClick={openEdit} className="btn-icon btn-icon-sm" aria-label="Editar" title="Editar">
        <Pencil size={13} />
      </button>
    ) : (
      <>
        <button
          type="button"
          onClick={cancelForm}
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
    <DetailSectionTemplate sectionTitle={SECTION_TITLE} listPath={LIST_PATH} record={{ id: data.id, name: data.label }} actions={actions}>
      {update.isError && <p className="text-red-600 dark:text-red-400 text-sm mb-4">{getErrorMessage(update.error)}</p>}

      {viewState === 'view' && <SectionRecordView groups={recordGroups(data)} />}

      {viewState === 'edit' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
              Agente responsable
            </h3>
            <div className="space-y-3">
              <ThemedSelect
                aria-label="Agente responsable del chat contextual"
                value={agentId}
                onChange={setAgentId}
                options={agentOptions}
                placeholder="— Agente —"
                allowEmpty={false}
              />
              <p className="text-xs text-text-muted">
                Solo perfiles de nivel 2 pueden llevar el chat contextual de una vista.
              </p>
            </div>
          </div>

          <div>
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
              Instrucciones del sidebar
            </h3>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={6}
              className="input-field text-sm"
              aria-label="Instrucciones de la vista"
            />
          </div>

          <button
            type="button"
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-text-secondary hover:bg-glass hover:text-text transition-colors disabled:opacity-50"
            disabled={(!data.responsible_agent_profile_id && !data.instructions) || isSaving}
            onClick={resetToDefault}
          >
            <RotateCcw size={15} aria-hidden="true" />
            Quitar responsable e instrucciones
          </button>
        </div>
      )}
    </DetailSectionTemplate>
  )
}

export default AdminViewsPage
