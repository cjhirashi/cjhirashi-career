import React, { useEffect, useId, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Check, ClipboardList, Pencil, Play, Plus, Trash2, X } from 'lucide-react'
import { useTaskMutations, useTasks } from '@/hooks/useTasks'
import { useAuthStore } from '@/stores/authStore'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { SectionViewTab } from '@/components/SectionViewTabs'
import { SectionShell } from '@/components/section'
import { getErrorMessage } from '@/utils/errors'
import { Task, TaskPayload, TaskStatus } from '@/types/tasks'
import { TaskForm, TASK_FORM_ID } from '@/components/tasks/TaskForm'
import { TaskRecordView } from '@/components/tasks/TaskRecordView'
import { TaskListView } from '@/components/tasks/TaskListView'
import { TaskKanbanView } from '@/components/tasks/TaskKanbanView'
import { TaskCalendarView } from '@/components/tasks/TaskCalendarView'
import { TaskGanttView } from '@/components/tasks/TaskGanttView'
import { groupSubtasks, isRootTask, AssigneeContext } from '@/components/tasks/taskUtils'

const BOARD_VIEW_TABS: SectionViewTab[] = [
  { key: 'list', label: 'Lista' },
  { key: 'kanban', label: 'Kanban' },
  { key: 'calendar', label: 'Calendario' },
  { key: 'gantt', label: 'Gantt' },
]

const RECORD_VIEW_TABS: SectionViewTab[] = [
  { key: 'list', label: 'Lista' },
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
  const { data: tasks, isLoading, isError, error } = useTasks()
  const { createMutation, updateMutation, deleteMutation } = useTaskMutations()
  const [recordState, setRecordState] = useState<RecordState>('board')
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const formOpenGuardAt = useRef(0)

  const user = useAuthStore((state) => state.user)
  const assignees = useMemo<AssigneeContext>(() => {
    return {
      userName: user?.full_name?.trim() || user?.username || 'Usuario',
      userPhoto: user?.photo_url ?? null,
    }
  }, [user])

  const list = tasks ?? []
  const roots = useMemo(() => list.filter(isRootTask), [list])
  const childrenByParent = useMemo(() => groupSubtasks(list), [list])
  const subtaskCount = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const [parentId, children] of childrenByParent) {
      counts[parentId] = children.length
    }
    return counts
  }, [childrenByParent])
  const datedTasks = useMemo(
    () =>
      list.map((task) =>
        task.parent_id ? { ...task, title: `↳ ${task.title}` } : task
      ),
    [list]
  )
  const deepLinkId = searchParams.get('task')

  useEffect(() => {
    if (!deepLinkId || list.length === 0) return
    const found = list.find((task) => task.id === deepLinkId)
    if (found) {
      setActiveTask(found)
      setRecordState('view')
    }
  }, [deepLinkId, list])

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

  const openView = (task: Task) => {
    setActiveTask(task)
    setRecordState('view')
  }

  const openEdit = (task: Task) => {
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

  const handleSave = async (payload: TaskPayload & { title: string }) => {
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

  const handleDelete = (task: Task) => {
    if (!window.confirm(`¿Eliminar la tarea "${task.title}"?`)) return
    deleteMutation.mutate(task.id)
    if (activeTask?.id === task.id) backToBoard()
  }

  const handleStatus = (task: Task, status: TaskStatus) => {
    updateMutation.mutate({ id: task.id, payload: { status } })
  }

  const submitTaskForm = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (isGhostFormOpenClick(event)) return
    const form = document.getElementById(formId) ?? document.getElementById(TASK_FORM_ID)
    if (form instanceof HTMLFormElement) form.requestSubmit()
  }

  const isBoard = recordState === 'board'
  const isSaving = createMutation.isPending || updateMutation.isPending
  const activeViewKey = isBoard ? boardView : recordState === 'view' ? 'view' : 'edit'
  const visibleTabs = isBoard ? BOARD_VIEW_TABS : RECORD_VIEW_TABS
  const interactiveKeys = isBoard ? BOARD_VIEW_KEYS : ['list']

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
    <SectionShell
      title={recordState === 'create' ? 'Tareas · nuevo' : 'Tareas'}
      count={isBoard && !isLoading ? roots.length : undefined}
      breadcrumb={
        showRecordHeading && headingTask
          ? { section: 'Tareas', id: headingTask.id, name: headingTask.title }
          : undefined
      }
      tabs={visibleTabs}
      activeTab={activeViewKey}
      interactiveTabs={interactiveKeys}
      onTabSelect={selectSectionView}
      actions={headerActions}
      variant={isBoard && boardView === 'list' ? 'list' : 'record'}
    >
          {isBoard && isLoading && <LoadingSpinner fullScreen={false} message="Cargando tareas..." />}
          {isBoard && isError && (
            <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
          )}

          {isBoard && !isLoading && !isError && list.length === 0 && boardView !== 'list' && (
            <div className="py-8 text-center">
              <ClipboardList className="mx-auto text-text-muted mb-2" size={28} aria-hidden="true" />
              <p className="text-text-secondary text-sm">
                Aún no hay tareas. Crea una con fecha y hora.
              </p>
            </div>
          )}

          {isBoard && !isLoading && !isError && boardView === 'list' && (
            <TaskListView
              tasks={roots}
              assignees={assignees}
              subtaskCount={subtaskCount}
              onOpen={openView}
              onEdit={openEdit}
              onDelete={handleDelete}
            />
          )}
          {isBoard && !isLoading && roots.length > 0 && boardView === 'kanban' && (
            <TaskKanbanView
              tasks={roots}
              assignees={assignees}
              onOpen={openView}
              onStatus={handleStatus}
              onDelete={handleDelete}
            />
          )}
          {isBoard && !isLoading && list.length > 0 && boardView === 'calendar' && (
            <TaskCalendarView tasks={datedTasks} onOpen={openView} />
          )}
          {isBoard && !isLoading && list.length > 0 && boardView === 'gantt' && (
            <TaskGanttView tasks={datedTasks} assignees={assignees} onOpen={openView} />
          )}

          {recordState === 'view' && activeTask && (
            <TaskRecordView
              task={activeTask}
              subtasks={childrenByParent.get(activeTask.id) ?? []}
              assignees={assignees}
              onStatus={handleStatus}
              onOpenSubtask={openView}
            />
          )}
          {(recordState === 'edit' || recordState === 'create') && (
            <TaskForm
              task={recordState === 'create' ? null : activeTask}
              subtasks={activeTask ? childrenByParent.get(activeTask.id) ?? [] : []}
              onSave={handleSave}
              isSaving={isSaving}
              formId={formId}
              hideActions
              onCancel={cancelForm}
            />
          )}
    </SectionShell>
  )
}

