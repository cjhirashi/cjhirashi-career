import React, { useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChevronDown, ChevronRight, ChevronUp, GripVertical } from 'lucide-react'
import {
  useAdminSection,
  useAdminSectionGroupReorder,
  useAdminSectionsReorder,
  useNavTree,
} from '@/hooks/useNavTree'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { SelectCapsule, SelectCapsuleGroup } from '@/components/SelectCapsule'
import { getErrorMessage } from '@/utils/errors'
import {
  ADMIN_SECTION_TYPE_LABEL,
  FlatNavSection,
  NavGroup,
  NavSection,
  flattenNavTree,
} from '@/types/adminSections'
import {
  DetailSectionTemplate,
  SectionRecordView,
  SectionShell,
} from '@/components/section'

const SECTION_TITLE = 'Secciones del Admin'
const LIST_PATH = '/settings/sections'

// ===========================================================================
// Lista — árbol de navegación (grupo → L1 → L2 → L3)
// ===========================================================================

const LEVEL_INDENT: Record<number, string> = {
  1: 'pl-0',
  2: 'pl-6',
  3: 'pl-12',
}

/** Up/down reorder within the same container — no drag-and-drop needed for
 * "reorder within the same level" (ADR-023 contrato §3.3; cross-level
 * re-parent is deferred to a follow-up). */
const MoveButtons: React.FC<{
  disabledUp: boolean
  disabledDown: boolean
  onMoveUp: () => void
  onMoveDown: () => void
  label: string
  pending?: boolean
}> = ({ disabledUp, disabledDown, onMoveUp, onMoveDown, label, pending }) => (
  <span className="inline-flex items-center gap-0.5" onClick={(e) => e.stopPropagation()}>
    <button
      type="button"
      className="btn-icon btn-icon-sm btn-icon-muted"
      aria-label={`Subir ${label}`}
      title={`Subir ${label}`}
      disabled={disabledUp || pending}
      onClick={onMoveUp}
    >
      <ChevronUp size={13} />
    </button>
    <button
      type="button"
      className="btn-icon btn-icon-sm btn-icon-muted"
      aria-label={`Bajar ${label}`}
      title={`Bajar ${label}`}
      disabled={disabledDown || pending}
      onClick={onMoveDown}
    >
      <ChevronDown size={13} />
    </button>
  </span>
)

const SectionRow: React.FC<{
  section: NavSection
  siblings: NavSection[]
  containerId: string
  onOpen: (id: string) => void
}> = ({ section, siblings, containerId, onOpen }) => {
  const reorder = useAdminSectionsReorder()
  const index = siblings.findIndex((s) => s.id === section.id)

  const moveBy = (delta: number) => {
    const order = siblings.map((s) => s.id)
    const target = index + delta
    if (target < 0 || target >= order.length) return
    ;[order[index], order[target]] = [order[target], order[index]]
    reorder.mutate({ container_id: containerId, order })
  }

  return (
    <>
      <tr className="cursor-pointer hover:bg-glass transition-colors" onClick={() => onOpen(section.id)}>
        <td className={`py-2 pr-3 ${LEVEL_INDENT[section.level] ?? ''}`}>
          <div className="flex items-center gap-2 min-w-0">
            <ChevronRight size={13} className="text-text-muted flex-shrink-0" aria-hidden="true" />
            <span className="text-sm text-text truncate">{section.label}</span>
          </div>
        </td>
        <td className="py-2 pr-3">
          <span className="mono text-primary text-xs">{section.id}</span>
        </td>
        <td className="py-2 pr-3">
          <span className="mono text-xs text-text-secondary">{section.system_name}</span>
        </td>
        <td className="py-2 pr-3">
          <SelectCapsuleGroup>
            <SelectCapsule
              code={section.section_type}
              label={ADMIN_SECTION_TYPE_LABEL[section.section_type] ?? section.section_type}
            />
          </SelectCapsuleGroup>
        </td>
        <td className="py-2 pr-3 text-xs text-text-secondary">{section.path || '—'}</td>
        <td className="py-2 pr-3 text-xs text-text-secondary text-right">{section.view_count}</td>
        <td className="py-2 pr-3 text-xs text-text-secondary text-right">{section.sort_order}</td>
        <td className="py-2 pr-1 text-right">
          <MoveButtons
            label={section.label}
            disabledUp={index <= 0}
            disabledDown={index === -1 || index >= siblings.length - 1}
            pending={reorder.isPending}
            onMoveUp={() => moveBy(-1)}
            onMoveDown={() => moveBy(1)}
          />
        </td>
      </tr>
      {section.children.map((child) => (
        <SectionRow
          key={child.id}
          section={child}
          siblings={section.children}
          containerId={section.id}
          onOpen={onOpen}
        />
      ))}
    </>
  )
}

const GroupBlock: React.FC<{
  group: NavGroup
  siblings: NavGroup[]
  onOpen: (id: string) => void
}> = ({ group, siblings, onOpen }) => {
  const reorderGroups = useAdminSectionGroupReorder()
  const index = siblings.findIndex((g) => g.id === group.id)

  const moveBy = (delta: number) => {
    const order = siblings.map((g) => g.id)
    const target = index + delta
    if (target < 0 || target >= order.length) return
    ;[order[index], order[target]] = [order[target], order[index]]
    reorderGroups.mutate(order)
  }

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 px-1 py-2">
        <GripVertical size={13} className="text-text-muted" aria-hidden="true" />
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
          {group.name}
        </h3>
        <span className="mono text-[10px] text-text-muted">{group.id}</span>
        <span className="ml-auto">
          <MoveButtons
            label={`grupo ${group.name}`}
            disabledUp={index <= 0}
            disabledDown={index === -1 || index >= siblings.length - 1}
            pending={reorderGroups.isPending}
            onMoveUp={() => moveBy(-1)}
            onMoveDown={() => moveBy(1)}
          />
        </span>
      </div>
      <table className="w-full text-left">
        <thead>
          <tr className="text-[11px] text-text-muted uppercase tracking-wide border-b border-border">
            <th className="py-1.5 pr-3 font-medium">Sección</th>
            <th className="py-1.5 pr-3 font-medium">ID</th>
            <th className="py-1.5 pr-3 font-medium">Nombre de sistema</th>
            <th className="py-1.5 pr-3 font-medium">Tipo</th>
            <th className="py-1.5 pr-3 font-medium">Ruta</th>
            <th className="py-1.5 pr-3 font-medium text-right">Vistas</th>
            <th className="py-1.5 pr-3 font-medium text-right">Orden</th>
            <th className="py-1.5 pr-1 font-medium text-right">Mover</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {group.sections.length === 0 ? (
            <tr>
              <td colSpan={8} className="py-3 text-sm text-text-muted">
                Sin secciones en este grupo.
              </td>
            </tr>
          ) : (
            group.sections.map((section) => (
              <SectionRow
                key={section.id}
                section={section}
                siblings={group.sections}
                containerId={group.id}
                onOpen={onOpen}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

export const AdminSectionsPage: React.FC = () => {
  const navigate = useNavigate()
  const { data, isLoading, isError, error } = useNavTree()

  const totalSections = useMemo(() => flattenNavTree(data).length, [data])

  const openSection = (id: string) => navigate(`${LIST_PATH}/${id}`)

  return (
    <SectionShell
      title={SECTION_TITLE}
      count={isLoading ? undefined : totalSections}
      tabs={[]}
      activeTab="list"
      variant="list"
    >
      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando árbol de secciones..." />}
      {isError && (
        <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
      )}
      {!isLoading && !isError && (
        <>
          <p className="text-sm text-text-secondary mb-4">
            Árbol del sidebar izquierdo: grupo → sección de primer nivel → subsección → sub-subsección.
            Usa las flechas de "Mover" para reordenar grupos o secciones dentro de su mismo
            contenedor. El anidamiento entre niveles (mover una sección L1 a L2, por ejemplo) llega
            en un follow-up. El agente responsable y las instrucciones se editan por{' '}
            <span className="text-text">vista</span> en{' '}
            <button
              type="button"
              className="text-primary hover:underline"
              onClick={() => navigate('/settings/views')}
            >
              Settings → Vistas
            </button>
            .
          </p>
          {(data?.groups ?? []).length === 0 ? (
            <p className="text-text-secondary text-sm">No hay grupos configurados.</p>
          ) : (
            <div className="table-scroll table-scroll-inset">
              {data?.groups.map((group) => (
                <GroupBlock
                  key={group.id}
                  group={group}
                  siblings={data.groups}
                  onOpen={openSection}
                />
              ))}
            </div>
          )}
        </>
      )}
    </SectionShell>
  )
}

// ===========================================================================
// Detalle — una sección (L1/L2/L3): metadatos + sus vistas (solo lectura,
// se editan desde Settings → Vistas) + reorden dentro del mismo nivel.
// ===========================================================================

const recordGroups = (data: FlatNavSection & { section_type: string; sort_order: number; origin: string }) => [
  {
    title: 'Información',
    fields: [
      { label: 'ID', value: <span className="mono text-primary">{data.id}</span> },
      {
        label: 'Nombre de sistema',
        value: <span className="mono text-primary">{data.system_name}</span>,
      },
      { label: 'Nivel', value: `L${data.level}` },
      {
        label: 'Tipo',
        value: (
          <SelectCapsule
            code={data.section_type}
            label={ADMIN_SECTION_TYPE_LABEL[data.section_type] ?? data.section_type}
          />
        ),
      },
      { label: 'Ruta', value: <span className="font-mono text-xs">{data.path || '—'}</span> },
      { label: 'Orden', value: data.sort_order },
      { label: 'Origen', value: data.origin },
      { label: 'Vistas', value: data.views.length },
    ],
  },
  {
    title: 'Vistas',
    fields:
      data.views.length === 0
        ? [{ label: 'Vistas', wide: true, value: 'Esta sección no tiene vistas (nodo de navegación).' }]
        : data.views.map((view) => ({
            label: view.label,
            wide: true,
            value: (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="mono text-xs text-text-secondary">{view.key}</span>
                <span className="mono text-xs text-primary">{view.id}</span>
                {view.chat_enabled && <SelectCapsule code="chat" label="Chat" />}
                {view.has_instructions && <SelectCapsule code="instrucciones" label="Instrucciones" />}
              </div>
            ),
          })),
  },
]

export const AdminSectionDetailPage: React.FC = () => {
  const navigate = useNavigate()
  const { sectionId = '' } = useParams<{ sectionId: string }>()
  const { data, isLoading, isError, error } = useAdminSection(sectionId)

  if (isLoading) return <LoadingSpinner fullScreen={false} message="Cargando sección..." />
  if (isError) return <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
  if (!data) return <p className="text-text-secondary">Sección no encontrada.</p>

  return (
    <DetailSectionTemplate
      sectionTitle={SECTION_TITLE}
      listPath={LIST_PATH}
      record={{ id: data.id, name: data.label }}
    >
      <SectionRecordView
        groups={recordGroups({
          id: data.id,
          level: data.level,
          system_name: data.system_name,
          label: data.label,
          path: data.path,
          views: data.views,
          section_type: data.section_type,
          sort_order: data.sort_order,
          origin: data.origin,
        })}
      />
      <div className="mt-6">
        <button
          type="button"
          className="text-sm text-primary hover:underline"
          onClick={() => navigate(`/settings/views?section_id=${data.id}`)}
        >
          Ver vistas de esta sección en Settings → Vistas →
        </button>
      </div>
    </DetailSectionTemplate>
  )
}

export default AdminSectionsPage
