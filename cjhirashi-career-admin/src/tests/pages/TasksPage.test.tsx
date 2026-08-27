import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent, waitFor } from '../utils'
import { TasksPage } from '@/pages/TasksPage'
import { agentTasksApi } from '@/api/agentTasks'
import { bedrockApi } from '@/api/bedrock'
import { mockUser } from '../fixtures/mockData'
import { useAuthStore } from '@/stores/authStore'
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
  parent_id: null,
  sort_order: 0,
  is_blocking: true,
  execute_on_turn: false,
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
    useAuthStore.setState({ user: mockUser })
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
        photo_url: 'https://example.com/agent.png',
      } as never,
    ])
  })

  it('shows the task in the list view', async () => {
    renderPage()
    expect(await screen.findByText('Buscar vacantes DevOps')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('Control de búsqueda de vacantes')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/buscar en tareas/i)).toBeInTheDocument()
    expect(screen.getByText('btk-1')).toBeInTheDocument()
    expect(screen.getByText('Pendiente')).toBeInTheDocument()
    expect(screen.getByText('Alta')).toBeInTheDocument()
    expect(screen.queryByText('pending')).not.toBeInTheDocument()
    expect(screen.queryByText('high')).not.toBeInTheDocument()
    expect(screen.getByText('Pendiente').closest('[data-tone]')).toHaveAttribute('data-tone', 'pending')
    expect(screen.getByText('Alta').closest('[data-tone]')).toHaveAttribute('data-tone', 'high')
    const assignee = screen.getByText('Control de búsqueda de vacantes').closest('.actor-capsule')
    expect(assignee).toBeTruthy()
    expect(assignee?.querySelector('img')?.getAttribute('src')).toBe('https://example.com/agent.png')
    expect(screen.queryByText('agent_vacancy_search')).not.toBeInTheDocument()
  })

  it('shows a user assignee as photo + name, not the user|Tú chip', async () => {
    mockedTasksApi.list.mockResolvedValue([
      { ...sampleTask, assignee_type: 'user', agent_profile_id: null },
    ])
    useAuthStore.setState({
      user: { ...mockUser, photo_url: 'https://example.com/me.jpg' },
    })
    renderPage()
    await screen.findByText('Buscar vacantes DevOps')
    const chip = screen.getByText('Demo User').closest('.actor-capsule')
    expect(chip).toBeTruthy()
    expect(chip?.querySelector('img')?.getAttribute('src')).toBe('https://example.com/me.jpg')
    expect(screen.queryByText('Tú')).not.toBeInTheDocument()
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
    expect(screen.getByRole('tab', { name: 'Kanban' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Calendario' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Gantt' })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Vista' })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Edición' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Nuevo' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Edición' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Lista' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Vista' })).toHaveClass('is-indicator')
    expect(screen.queryByRole('tab', { name: 'Kanban' })).not.toBeInTheDocument()
    expect(screen.getByLabelText(/responsable/i)).toBeInTheDocument()
    expect(screen.getAllByText('Demo User').length).toBeGreaterThan(0)
    expect(screen.queryByText(/Tú \(manual\)/)).not.toBeInTheDocument()
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
    expect(screen.queryByRole('tab', { name: 'Kanban' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.getByRole('heading', { name: /Información/ })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Vista' })).toHaveAttribute('aria-selected', 'true')

    fireEvent.click(screen.getByRole('tab', { name: 'Lista' }))
    expect(screen.getByRole('tab', { name: 'Kanban' })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Vista' })).not.toBeInTheDocument()
  })

  it('changes status from the record view without entering edit', async () => {
    renderPage()
    fireEvent.click(await screen.findByText('Buscar vacantes DevOps'))
    fireEvent.click(screen.getByRole('button', { name: 'Estado de Buscar vacantes DevOps' }))
    fireEvent.click(screen.getByRole('option', { name: /Hecha/i }))
    await waitFor(() =>
      expect(mockedTasksApi.update).toHaveBeenCalledWith(
        'btk-1',
        expect.objectContaining({ status: 'done' })
      )
    )
  })

  it('lists subtasks on the parent record view', async () => {
    mockedTasksApi.list.mockResolvedValue([
      sampleTask,
      {
        ...sampleTask,
        id: 'btk-2',
        parent_id: 'btk-1',
        title: 'Revisar resultados',
        assignee_type: 'user',
        agent_profile_id: null,
        sort_order: 0,
        is_blocking: true,
      },
    ])
    renderPage()
    fireEvent.click(await screen.findByText('Buscar vacantes DevOps'))
    expect(screen.getByRole('heading', { name: /Subtareas/ })).toBeInTheDocument()
    expect(screen.getByText('1. Revisar resultados')).toBeInTheDocument()
  })

  it('shows an empty state when there are no tasks', async () => {
    mockedTasksApi.list.mockResolvedValue([])
    renderPage()
    await waitFor(() => expect(screen.getByText(/aún no hay tareas/i)).toBeInTheDocument())
  })
})
