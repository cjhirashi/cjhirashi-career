import React, { useEffect, useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown, Pencil, Play, Search, Trash2, X } from 'lucide-react'
import { BedrockTask } from '@/types/bedrock'
import { ColumnConfig, SelectOption } from '@/config/careerResources'
import { formatCellValue } from '@/components/career/careerFieldUtils'
import { TableColumnSettings } from '@/components/career/TableColumnSettings'
import { useVisibleTableColumns } from '@/hooks/useVisibleTableColumns'
import { ThemedMultiSelect } from '@/components/ThemedMultiSelect'
import { PersonChip } from '@/components/PersonAvatar'
import { formatDateTime } from '@/utils/formatters'
import {
  assigneeDisplay,
  assigneeLabel,
  AssigneeContext,
  canRunAgentTask,
  TASK_PRIORITY_LABELS,
  TASK_STATUS_LABELS,
} from './taskUtils'

const TASK_COLUMNS: ColumnConfig[] = [
  { key: 'id', label: 'ID' },
  { key: 'title', label: 'Tarea' },
  { key: 'assignee', label: 'Asignada a' },
  { key: 'status', label: 'Estado' },
  { key: 'scheduled_at', label: 'Inicio', format: 'datetime' },
  { key: 'due_at', label: 'Límite', format: 'datetime' },
  { key: 'priority', label: 'Prioridad' },
]

const TASK_PINNED = ['id', 'title']
const DEFAULT_KEYS = TASK_COLUMNS.map((col) => col.key)

const STATUS_OPTIONS: SelectOption[] = Object.entries(TASK_STATUS_LABELS).map(([value, label]) => ({
  value,
  label,
}))

const PRIORITY_OPTIONS: SelectOption[] = Object.entries(TASK_PRIORITY_LABELS).map(([value, label]) => ({
  value,
  label,
}))

const ASSIGNEE_TYPE_OPTIONS_BASE: SelectOption[] = [{ value: 'agent', label: 'Agente' }]

type TaskFilters = {
  status: string[]
  assignee_type: string[]
  priority: string[]
}

const EMPTY_FILTERS: TaskFilters = { status: [], assignee_type: [], priority: [] }

interface TaskListViewProps {
  tasks: BedrockTask[]
  assignees: AssigneeContext
  subtaskCount?: Record<string, number>
  onOpen: (task: BedrockTask) => void
  onEdit: (task: BedrockTask) => void
  onDelete: (task: BedrockTask) => void
  onRun: (task: BedrockTask) => void
  runningId?: string
}

const cellValue = (task: BedrockTask, key: string, assignees: AssigneeContext): unknown => {
  if (key === 'assignee') return assigneeLabel(task, assignees)
  return task[key as keyof BedrockTask]
}

const compareCells = (a: unknown, b: unknown, dir: 'asc' | 'desc'): number => {
  const av = a == null ? '' : String(a).toLowerCase()
  const bv = b == null ? '' : String(b).toLowerCase()
  const cmp = av.localeCompare(bv, 'es', { numeric: true })
  return dir === 'asc' ? cmp : -cmp
}

export const TaskListView: React.FC<TaskListViewProps> = ({
  tasks,
  assignees,
  subtaskCount = {},
  onOpen,
  onEdit,
  onDelete,
  onRun,
  runningId,
}) => {
  const { columns, selectedKeys, toggleColumn, moveColumn, options, pinnedKeys } = useVisibleTableColumns(
    'agent-tasks',
    TASK_COLUMNS,
    DEFAULT_KEYS,
    TASK_PINNED
  )
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<string | undefined>(undefined)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [filters, setFilters] = useState<TaskFilters>(EMPTY_FILTERS)

  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(searchInput.trim().toLowerCase()), 300)
    return () => window.clearTimeout(timer)
  }, [searchInput])

  const filtersActive = filters.status.length + filters.assignee_type.length + filters.priority.length > 0

  const assigneeTypeOptions: SelectOption[] = [
    { value: 'user', label: assignees.userName },
    ...ASSIGNEE_TYPE_OPTIONS_BASE,
  ]

  const rows = useMemo(() => {
    let next = tasks
    if (search) {
      next = next.filter((task) => {
        const haystack = [
          task.id,
          task.title,
          task.description,
          assigneeLabel(task, assignees),
          TASK_STATUS_LABELS[task.status],
          TASK_PRIORITY_LABELS[task.priority],
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        return haystack.includes(search)
      })
    }
    if (filters.status.length) next = next.filter((task) => filters.status.includes(task.status))
    if (filters.assignee_type.length) {
      next = next.filter((task) => filters.assignee_type.includes(task.assignee_type))
    }
    if (filters.priority.length) next = next.filter((task) => filters.priority.includes(task.priority))
    if (sortBy) {
      next = [...next].sort((a, b) =>
        compareCells(cellValue(a, sortBy, assignees), cellValue(b, sortBy, assignees), sortDir)
      )
    }
    return next
  }, [tasks, search, filters, sortBy, sortDir, assignees])

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

  const filterFor = (key: string) => {
    if (key === 'status') {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Estado"
          value={filters.status}
          onChange={(status) => setFilters((current) => ({ ...current, status }))}
          options={STATUS_OPTIONS}
        />
      )
    }
    if (key === 'assignee') {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Asignada a"
          value={filters.assignee_type}
          onChange={(assignee_type) => setFilters((current) => ({ ...current, assignee_type }))}
          options={assigneeTypeOptions}
        />
      )
    }
    if (key === 'priority') {
      return (
        <ThemedMultiSelect
          variant="icon"
          aria-label="Prioridad"
          value={filters.priority}
          onChange={(priority) => setFilters((current) => ({ ...current, priority }))}
          options={PRIORITY_OPTIONS}
        />
      )
    }
    return null
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-secondary" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Buscar en tareas..."
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
          <button type="button" className="btn-secondary btn-small" onClick={() => setFilters(EMPTY_FILTERS)}>
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
        search || filtersActive ? (
          <p className="text-text-secondary text-sm text-center py-6">
            Sin resultados para esa búsqueda o filtros.
          </p>
        ) : (
          <div className="py-8 text-center">
            <p className="text-text-secondary text-sm">
              Aún no hay tareas. Crea una para ti o asígnasela a un agente con fecha y hora.
            </p>
          </div>
        )
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
                          sortDir === 'asc' ? (
                            <ArrowUp size={12} />
                          ) : (
                            <ArrowDown size={12} />
                          )
                        ) : (
                          <ArrowUpDown size={12} className="opacity-30" />
                        )}
                      </button>
                      {filterFor(col.key)}
                    </span>
                  </th>
                ))}
                <th className="px-6 py-2 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((task) => (
                <tr
                  key={task.id}
                  className="border-b border-border last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer"
                  onClick={() => onOpen(task)}
                >
                  {columns.map((col) => {
                    if (col.key === 'id') {
                      return (
                        <td key="id" className="px-6 py-2 table-col-id" title={task.id}>
                          {task.id}
                        </td>
                      )
                    }
                    if (col.key === 'status') {
                      return (
                        <td key={col.key} className="px-6 py-2">
                          <StateCapsule
                            tone={task.status}
                            label={TASK_STATUS_LABELS[task.status] ?? task.status}
                          />
                        </td>
                      )
                    }
                    if (col.key === 'priority') {
                      return (
                        <td key={col.key} className="px-6 py-2">
                          <StateCapsule
                            tone={task.priority}
                            label={TASK_PRIORITY_LABELS[task.priority] ?? task.priority}
                          />
                        </td>
                      )
                    }
                    if (col.key === 'assignee') {
                      const person = assigneeDisplay(task, assignees)
                      return (
                        <td key={col.key} className="px-6 py-2">
                          <PersonChip src={person.imageUrl} name={person.name} />
                        </td>
                      )
                    }
                    if (col.key === 'scheduled_at' || col.key === 'due_at') {
                      const iso = col.key === 'scheduled_at' ? task.scheduled_at : task.due_at
                      return (
                        <td key={col.key} className="px-6 py-2 whitespace-nowrap text-text">
                          {iso ? formatDateTime(iso) : '—'}
                        </td>
                      )
                    }
                    return (
                      <td key={col.key} className="px-6 py-2 whitespace-nowrap text-text">
                        {formatCellValue(cellValue(task, col.key, assignees), col.format)}
                        {col.key === 'title' && (subtaskCount[task.id] ?? 0) > 0 && (
                          <span className="ml-2 text-[11px] text-text-muted">
                            {subtaskCount[task.id]} subtarea{subtaskCount[task.id] === 1 ? '' : 's'}
                          </span>
                        )}
                      </td>
                    )
                  })}
                  <td className="px-6 py-2 text-right whitespace-nowrap" onClick={(event) => event.stopPropagation()}>
                    <div className="flex justify-end items-center gap-1">
                      {canRunAgentTask(task) && (subtaskCount[task.id] ?? 0) === 0 && (
                        <button
                          type="button"
                          className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
                          aria-label={`Ejecutar "${task.title}"`}
                          title="Ejecutar ahora"
                          disabled={runningId === task.id}
                          onClick={() => onRun(task)}
                        >
                          <Play size={15} />
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => onEdit(task)}
                        aria-label="Editar"
                        className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(task)}
                        aria-label={`Eliminar "${task.title}"`}
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
    </>
  )
}
