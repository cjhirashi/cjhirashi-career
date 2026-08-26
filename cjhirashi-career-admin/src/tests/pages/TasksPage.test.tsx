import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent, waitFor } from '../utils'
import { TasksPage } from '@/pages/TasksPage'
import { agentTasksApi } from '@/api/agentTasks'
import { bedrockApi } from '@/api/bedrock'
import { BedrockTask } from '@/types/bedrock'

vi.mock('@/api/agentTasks')
vi.mock('@/api/bedrock', () => ({
  bedrockApi: { listAgentCatalog: vi.fn() },
}))

const mockedTasksApi = vi.mocked(agentTasksApi)
const mockedBedrockApi = vi.mocked(bedrockApi)

const sampleTask: BedrockTask = {
  id: 'btk-1',
  user_id: 'usr-1',
  title: 'Buscar vacantes DevOps',
  description: 'Indeed y RemoteOK',
  status: 'pending',
  notes: null,
  assignee_type: 'agent',
  agent_profile_id: 'agent_vacancy_search',
  scheduled_at: '2026-08-27T15:00:00Z',
  due_at: '2026-08-27T18:00:00Z',
  priority: 'high',
  execution_result: null,
  executed_at: null,
  error_message: null,
  created_at: '2026-08-26T00:00:00Z',
  updated_at: '2026-08-26T00:00:00Z',
}

const renderPage = (path = '/tasks') =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <TasksPage />
    </MemoryRouter>
  )

describe('TasksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedTasksApi.list.mockResolvedValue([sampleTask])
    mockedTasksApi.count.mockResolvedValue(1)
    mockedTasksApi.create.mockResolvedValue(sampleTask)
    mockedTasksApi.update.mockResolvedValue(sampleTask)
    mockedBedrockApi.listAgentCatalog.mockResolvedValue([
      {
        profile_id: 'agent_vacancy_search',
        label: 'Control de búsqueda de vacantes',
        level: 3,
        user_facing: false,
      } as never,
    ])
  })

  it('shows the task in the list view', async () => {
    renderPage()
    expect(await screen.findByText('Buscar vacantes DevOps')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('Control de búsqueda de vacantes')).toBeInTheDocument()
  })

  it('switches to kanban, calendar and gantt', async () => {
    renderPage()
    await screen.findByText('Buscar vacantes DevOps')

    fireEvent.click(screen.getByRole('tab', { name: 'Kanban' }))
    expect(screen.getByRole('heading', { name: /Pendiente/ })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Calendario' }))
    expect(screen.getByRole('button', { name: 'Hoy' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Gantt' }))
    expect(screen.getAllByText('Buscar vacantes DevOps').length).toBeGreaterThan(0)
  })

  it('uses table-section chrome: title, folder tabs and an icon action on the tab row', async () => {
    renderPage()
    await screen.findByText('Buscar vacantes DevOps')
    expect(screen.getByRole('heading', { name: /Tareas/ })).toBeInTheDocument()
    expect(screen.queryByText(/aunque no estés en sesión/)).not.toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveClass('view-tab')
    expect(screen.getByRole('tab', { name: 'Vista' })).toHaveClass('is-indicator')
    expect(screen.getByRole('tab', { name: 'Edición' })).toHaveClass('is-indicator')
    fireEvent.click(screen.getByRole('button', { name: 'Nuevo' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Edición' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByLabelText(/asignada a/i)).toBeInTheDocument()
  })

  it('opens record and edit views when a task is selected', async () => {
    renderPage()
    fireEvent.click(await screen.findByText('Buscar vacantes DevOps'))

    expect(screen.getByRole('tab', { name: 'Vista' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('heading', { name: /Información/ })).toBeInTheDocument()
    expect(screen.getByText('Indeed y RemoteOK')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    expect(screen.getByRole('tab', { name: 'Edición' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByLabelText(/título/i)).toHaveValue('Buscar vacantes DevOps')

    fireEvent.click(screen.getByRole('tab', { name: 'Vista' }))
    expect(screen.getByRole('heading', { name: /Información/ })).toBeInTheDocument()
  })

  it('shows an empty state when there are no tasks', async () => {
    mockedTasksApi.list.mockResolvedValue([])
    renderPage()
    await waitFor(() => expect(screen.getByText(/aún no hay tareas/i)).toBeInTheDocument())
  })
})
