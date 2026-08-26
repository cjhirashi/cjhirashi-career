import React, { useEffect, useId, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Check, ClipboardList, Pencil, Play, Plus, Trash2, X } from 'lucide-react'
import { useAgentCatalog, useAgentTaskMutations, useAgentTasks } from '@/hooks/useBedrockChat'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { SectionViewTabs, SectionViewTab } from '@/components/SectionViewTabs'
import { getErrorMessage } from '@/utils/errors'
import { BedrockTask, BedrockTaskPayload, TaskStatus } from '@/types/bedrock'
import { TaskForm, TASK_FORM_ID } from '@/components/tasks/TaskForm'
import { TaskRecordView } from '@/components/tasks/TaskRecordView'
import { TaskListView } from '@/components/tasks/TaskListView'
import { TaskKanbanView } from '@/components/tasks/TaskKanbanView'
import { TaskCalendarView } from '@/components/tasks/TaskCalendarView'
import { TaskGanttView } from '@/components/tasks/TaskGanttView'
import { canRunAgentTask } from '@/components/tasks/taskUtils'

const BOARD_VIEW_TABS: SectionViewTab[] = [
  { key: 'list', label: 'Lista' },
  { key: 'kanban', label: 'Kanban' },
  { key: 'calendar', label: 'Calendario' },
  { key: 'gantt', label: 'Gantt' },
]

const TASK_VIEW_TABS: SectionViewTab[] = [
  ...BOARD_VIEW_TABS,
  { key: 'view', label: 'Vista' },
  { key: 'edit', label: 'Edición' },
]

type BoardViewId = (typeof BOARD_VIEW_TABS)[number]['key']
type RecordState = 'board' | 'view' | 'edit' | 'create'

const BOARD_VIEW_KEYS = BOARD_VIEW_TABS.map((tab) => tab.key)

const isBoardView = (value: string | null): value is BoardViewId =>
  BOARD_VIEW_TABS.some((tab) => tab.key === value)

export const TasksPage: React.FC = () => {
  const formId = useId()
  const [searchParams, setSearchParams] = useSearchParams()
  const boardView: BoardViewId = isBoardView(searchParams.get('view'))
    ? (searchParams.get('view') as BoardViewId)
    : 'list'
  const { data: tasks, isLoading, isError, error } = useAgentTasks()
  const { data: catalog } = useAgentCatalog()
  const { createMutation, updateMutation, deleteMutation, runMutation } = useAgentTaskMutations()
  const [recordState, setRecordState] = useState<RecordState>('board')
  const [activeTask, setActiveTask] = useState<BedrockTask | null>(null)
  const formOpenGuardAt = useRef(0)

  const agentLabels = useMemo(() => {
    const map: Record<string, string> = {}
    for (const agent of catalog ?? []) {
      map[agent.profile_id] = agent.label
    }
    return map
  }, [catalog])

  const list = tasks ?? []

  useEffect(() => {
    if (!activeTask) return
    const next = list.find((task) => task.id === activeTask.id)
    if (next && next !== activeTask) setActiveTask(next)
  }, [list, activeTask])

  const setBoardView = (next: string) => {
    if (!isBoardView(next)) return
    setSearchParams(next === 'list' ? {} : { view: next }, { replace: true })
  }

  const guardFormOpenFromClick = () => {
    formOpenGuardAt.current = performance.now()
  }

  const isGhostFormOpenClick = (event: { isTrusted: boolean }) =>
    event.isTrusted && performance.now() - formOpenGuardAt.current < 400

  const backToBoard = () => {
    setRecordState('board')
    setActiveTask(null)
  }

  const openView = (task: BedrockTask) => {
    setActiveTask(task)
    setRecordState('view')
  }

  const openEdit = (task: BedrockTask) => {
    guardFormOpenFromClick()
    setActiveTask(task)
    setRecordState('edit')
  }

  const openCreate = () => {
    guardFormOpenFromClick()
    setActiveTask(null)
    setRecordState('create')
  }

  const cancelForm = () => {
    if (activeTask) {
      setRecordState('view')
      return
    }
    backToBoard()
  }

  const selectSectionView = (key: string) => {
    if (isBoardView(key)) {
      setBoardView(key)
      setRecordState('board')
      setActiveTask(null)
      return
    }
    if (key === 'view' && activeTask) {
      setRecordState('view')
      return
    }
    if (key === 'edit' && activeTask) {
      openEdit(activeTask)
    }
  }

  const handleSave = async (payload: BedrockTaskPayload & { title: string }) => {
    if (recordState === 'edit' && activeTask) {
      const updated = await updateMutation.mutateAsync({ id: activeTask.id, payload })
      setActiveTask(updated)
      setRecordState('view')
      return
    }
    const created = await createMutation.mutateAsync(payload)
    setActiveTask(created)
    setRecordState('view')
  }

  const handleDelete = (task: BedrockTask) => {
    if (!window.confirm(`¿Eliminar la tarea "${task.title}"?`)) return
    deleteMutation.mutate(task.id)
    if (activeTask?.id === task.id) backToBoard()
  }

  const handleStatus = (task: BedrockTask, status: TaskStatus) => {
    updateMutation.mutate({ id: task.id, payload: { status } })
  }

  const handleRun = (task: BedrockTask) => {
    runMutation.mutate(task.id)
  }

  const submitTaskForm = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (isGhostFormOpenClick(event)) return
    const form = document.getElementById(formId) ?? document.getElementById(TASK_FORM_ID)
    if (form instanceof HTMLFormElement) form.requestSubmit()
  }

  const isBoard = recordState === 'board'
  const isSaving = createMutation.isPending || updateMutation.isPending
  const activeViewKey = isBoard ? boardView : recordState === 'view' ? 'view' : 'edit'
  const interactiveKeys =
    isBoard || recordState === 'create'
      ? BOARD_VIEW_KEYS
      : [...BOARD_VIEW_KEYS, 'view', 'edit']

  const headingTask = recordState === 'create' ? null : activeTask
  const showRecordHeading = !isBoard && Boolean(headingTask)

  const headerActions = isBoard ? (
    <button
      type="button"
      onClick={openCreate}
      className="btn-icon btn-icon-sm"
      aria-label="Nuevo"
      title="Nuevo"
    >
      <Plus size={13} />
    </button>
  ) : recordState === 'view' && activeTask ? (
    <>
      {canRunAgentTask(activeTask) && (
        <button
          type="button"
          onClick={() => handleRun(activeTask)}
          disabled={runMutation.isPending}
          className="btn-icon btn-icon-sm"
          aria-label="Ejecutar ahora"
          title="Ejecutar ahora"
        >
          <Play size={13} />
        </button>
      )}
      <button
        type="button"
        onClick={() => openEdit(activeTask)}
        className="btn-icon btn-icon-sm"
        aria-label="Editar"
        title="Editar"
      >
        <Pencil size={13} />
      </button>
      <button
        type="button"
        onClick={() => handleDelete(activeTask)}
        className="btn-icon btn-icon-sm btn-icon-danger"
        aria-label="Eliminar"
        title="Eliminar"
      >
        <Trash2 size={13} />
      </button>
    </>
  ) : recordState === 'edit' || recordState === 'create' ? (
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
        onClick={submitTaskForm}
        className="btn-icon btn-icon-sm"
        aria-label={recordState === 'create' ? 'Crear' : 'Actualizar'}
        title={recordState === 'create' ? 'Crear' : 'Actualizar'}
        disabled={isSaving}
      >
        <Check size={13} />
      </button>
    </>
  ) : null

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="card has-view-tabs">
        <div className="card-header">
          <h2 className="font-semibold text-text flex items-center gap-2 min-w-0">
            {showRecordHeading && headingTask ? (
              <>
                <span className="truncate">Tareas</span>
                <span className="text-text-muted font-normal">·</span>
                <span className="mono text-primary font-normal flex-shrink-0">{headingTask.id}</span>
                <span className="text-text-muted font-normal">·</span>
                <span className="truncate">{headingTask.title}</span>
              </>
            ) : recordState === 'create' ? (
              <span className="truncate">Tareas · nuevo</span>
            ) : (
              <>
                <span className="truncate">Tareas</span>
                {!isLoading && <span className="badge badge-slate mono">{list.length}</span>}
              </>
            )}
          </h2>
          <div className="view-tabs-row">
            <SectionViewTabs
              views={TASK_VIEW_TABS}
              activeKey={activeViewKey}
              interactiveKeys={interactiveKeys}
              onSelect={selectSectionView}
            />
            {headerActions ? <div className="view-tabs-actions">{headerActions}</div> : null}
          </div>
        </div>

        <div className="card-body">
          {isBoard && isLoading && <LoadingSpinner fullScreen={false} message="Cargando tareas..." />}
          {isBoard && isError && (
            <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
          )}

          {isBoard && !isLoading && !isError && list.length === 0 && (
            <div className="py-8 text-center">
              <ClipboardList className="mx-auto text-text-muted mb-2" size={28} aria-hidden="true" />
              <p className="text-text-secondary text-sm">
                Aún no hay tareas. Crea una para ti o asígnasela a un agente con fecha y hora.
              </p>
            </div>
          )}

          {isBoard && !isLoading && list.length > 0 && boardView === 'list' && (
            <TaskListView
              tasks={list}
              agentLabels={agentLabels}
              onOpen={openView}
              onDelete={handleDelete}
              onRun={handleRun}
              runningId={runMutation.isPending ? runMutation.variables : undefined}
            />
          )}
          {isBoard && !isLoading && list.length > 0 && boardView === 'kanban' && (
            <TaskKanbanView
              tasks={list}
              agentLabels={agentLabels}
              onOpen={openView}
              onStatus={handleStatus}
              onDelete={handleDelete}
            />
          )}
          {isBoard && !isLoading && list.length > 0 && boardView === 'calendar' && (
            <TaskCalendarView tasks={list} onOpen={openView} />
          )}
          {isBoard && !isLoading && list.length > 0 && boardView === 'gantt' && (
            <TaskGanttView tasks={list} agentLabels={agentLabels} onOpen={openView} />
          )}

          {recordState === 'view' && activeTask && (
            <TaskRecordView task={activeTask} agentLabels={agentLabels} />
          )}
          {(recordState === 'edit' || recordState === 'create') && (
            <TaskForm
              task={recordState === 'create' ? null : activeTask}
              agents={catalog ?? []}
              onSave={handleSave}
              isSaving={isSaving}
              formId={formId}
              hideActions
              onCancel={cancelForm}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export { TasksPage as AgentTasksPage }
