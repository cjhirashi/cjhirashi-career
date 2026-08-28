import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../utils'
import { Sidebar } from '@/components/Sidebar'
import { BrowserRouter } from 'react-router-dom'
import { careerApi } from '@/api/career'
import { filesApi } from '@/api/files'
import { agentTasksApi } from '@/api/agentTasks'
import { adminNavTreeApi } from '@/api/adminSections'
import { NavGroup, NavSection, NavTreeResponse, NavView } from '@/types/adminSections'

vi.mock('@/api/career', () => ({
  careerApi: { count: vi.fn() },
}))
vi.mock('@/api/files', () => ({
  filesApi: { count: vi.fn() },
}))
vi.mock('@/api/agentTasks', () => ({
  agentTasksApi: { count: vi.fn(), list: vi.fn() },
}))
vi.mock('@/api/adminSections')

const mockedCareerApi = vi.mocked(careerApi)
const mockedFilesApi = vi.mocked(filesApi)
const mockedAgentTasksApi = vi.mocked(agentTasksApi)
const mockedNavTree = vi.mocked(adminNavTreeApi)

// Mock useLocation to control current path
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useLocation: () => ({ pathname: '/dashboard' }),
  }
})

const view = (key: string, id: string): NavView => ({
  id,
  key,
  label: key,
  sort_order: 0,
  data_source: 'crud',
  resource_key: null,
  has_controls_window: false,
  tool_names: [],
  responsible_agent_profile_id: null,
  has_instructions: false,
  chat_enabled: false,
})

let seq = 0
const l1 = (
  systemName: string,
  label: string,
  path: string,
  sortOrder: number
): NavSection => {
  seq += 1
  return {
    id: `s1-${seq}`,
    level: 1,
    system_name: systemName,
    label,
    path,
    section_type: 'table',
    sort_order: sortOrder,
    origin: 'code',
    has_layout: true,
    view_count: 1,
    views: [view('list', `vw-${seq}`)],
    children: [],
  }
}

const group = (id: string, systemName: string, name: string, sortOrder: number, sections: NavSection[]): NavGroup => ({
  id,
  system_name: systemName,
  name,
  sort_order: sortOrder,
  sections,
})

// Mirror of cjhirashi-career-api/src/services/admin_sections.py (ADR-023),
// trimmed to the entries this suite asserts on.
const sampleTree: NavTreeResponse = {
  groups: [
    group('grp-1', 'metrics', 'Métricas', 10, [
      l1('dashboard', 'Dashboard', '/dashboard', 10),
      l1('metrics', 'Métricas', '/metrics', 11),
    ]),
    group('grp-2', 'principal', 'Principal', 15, [l1('agent-tasks', 'Tareas', '/tasks', 15)]),
    group('grp-3', 'storage', 'Almacenamiento', 20, [l1('files', 'Archivos', '/files', 20)]),
    group('grp-9', 'professional-identity', 'Identidad Profesional', 100, [
      l1('career-personal-profile', 'Datos personales', '/career/personal-profile', 100),
      l1('career-work-history', 'Historial Laboral', '/career/work-history', 107),
    ]),
    group('grp-5', 'search-ops', 'Operativa de Búsqueda', 31, [
      l1('job-discovery', 'Descubrir vacantes', '/job-discovery', 31),
      l1('career-vacancies', 'Vacantes', '/career/vacancies', 126),
    ]),
    group('grp-4', 'digital-presence', 'Presencia Digital', 30, [
      l1('linkedin-publish', 'LinkedIn · Publicar', '/linkedin', 30),
      l1('career-publications', 'Publicaciones', '/career/publications', 145),
    ]),
    group('grp-10', 'networking', 'Networking', 150, [
      l1('career-contact-interactions', 'Interacciones de contacto', '/career/contact-interactions', 150),
    ]),
    group('grp-11', 'support', 'Soporte', 160, [l1('career-tags', 'Tags', '/career/tags', 160)]),
  ],
  generated_at: '2026-08-28T12:00:00Z',
}

const renderSidebar = (isOpen: boolean, onToggle: () => void) => {
  return render(
    <BrowserRouter>
      <Sidebar isOpen={isOpen} onToggle={onToggle} />
    </BrowserRouter>
  )
}

describe('Sidebar', () => {
  const mockOnToggle = vi.fn()

  beforeEach(() => {
    mockOnToggle.mockClear()
    mockedCareerApi.count.mockResolvedValue(4)
    mockedFilesApi.count.mockResolvedValue(12)
    mockedAgentTasksApi.count.mockResolvedValue(3)
    mockedNavTree.get.mockResolvedValue(sampleTree)
  })

  describe('rendering', () => {
    it('should render sidebar element', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar).toBeInTheDocument()
    })

    it('should display the static menu items when open', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Dashboard')
      expect(screen.getByText('Métricas')).toBeInTheDocument()
      expect(screen.getByText('Archivos')).toBeInTheDocument()
      expect(screen.getByText('Tareas')).toBeInTheDocument()
    })

    it('should not render legacy (pre-career-domain) menu items anymore', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Dashboard')
      expect(screen.queryByText('Identity')).not.toBeInTheDocument()
      expect(screen.queryByText('Competencies')).not.toBeInTheDocument()
      expect(screen.queryByText('Evidence')).not.toBeInTheDocument()
      expect(screen.queryByText('Job Strategies')).not.toBeInTheDocument()
      expect(screen.queryByText('Interviews')).not.toBeInTheDocument()
    })

    it('should not show menu labels when closed', () => {
      renderSidebar(false, mockOnToggle)
      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
    })

    it('should show version number when open', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByText('v0.1.0')).toBeInTheDocument()
    })

    it('should not show version number when closed', () => {
      renderSidebar(false, mockOnToggle)
      expect(screen.queryByText('v0.1.0')).not.toBeInTheDocument()
    })
  })

  describe('toggle button', () => {
    it('should render toggle button', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByTitle('Contraer')).toBeInTheDocument()
    })

    it('should call onToggle when button clicked', () => {
      renderSidebar(true, mockOnToggle)
      fireEvent.click(screen.getByTitle('Contraer'))
      expect(mockOnToggle).toHaveBeenCalled()
    })

    it('should have correct title when closed', () => {
      renderSidebar(false, mockOnToggle)
      expect(screen.getByTitle('Expandir')).toBeInTheDocument()
    })
  })

  describe('static menu items and links', () => {
    it('should render the static top-level links', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByRole('link', { name: /Dashboard/i })
      expect(screen.getByRole('link', { name: /Dashboard/i })).toHaveAttribute('href', '/dashboard')
      expect(screen.getByRole('link', { name: /Métricas/i })).toHaveAttribute('href', '/metrics')
      const filesLink = screen.getByRole('link', { name: /Archivos/i })
      expect(filesLink).toHaveAttribute('href', '/files')
      await waitFor(() => expect(filesLink).toHaveAccessibleName('Archivos, 12 registros'))
      const tasksLink = screen.getByRole('link', { name: /Tareas/i })
      expect(tasksLink).toHaveAttribute('href', '/tasks')
      await waitFor(() => expect(tasksLink).toHaveAccessibleName('Tareas, 3 registros'))
    })

    it('should render a Lucide (svg) icon for each static link', async () => {
      renderSidebar(true, mockOnToggle)
      const dashboardLink = await screen.findByRole('link', { name: /Dashboard/i })
      expect(dashboardLink.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('active state styling', () => {
    it('should highlight the active menu item', async () => {
      renderSidebar(true, mockOnToggle)
      const dashboardLink = await screen.findByRole('link', { name: /Dashboard/i })
      expect(dashboardLink.className).toContain('is-active')
      expect(dashboardLink).toHaveAttribute('aria-current', 'page')
    })

    it('should not highlight inactive menu items', async () => {
      renderSidebar(true, mockOnToggle)
      const metricsLink = await screen.findByRole('link', { name: /Métricas/i })
      expect(metricsLink.className).not.toContain('is-active')
      expect(metricsLink).not.toHaveAttribute('aria-current')
    })

    it('should use the shared sidebar-item styling for every link', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByRole('link', { name: /Dashboard/i })
      expect(screen.getByRole('link', { name: /Dashboard/i }).className).toContain('sidebar-item')
      expect(screen.getByRole('link', { name: /Métricas/i }).className).toContain('sidebar-item')
    })
  })

  describe('sizing and layout', () => {
    it('should have wide width when open', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      expect(container.querySelector('aside')?.className).toContain('w-64')
    })

    it('should have narrow width when closed', () => {
      const { container } = renderSidebar(false, mockOnToggle)
      expect(container.querySelector('aside')?.className).toContain('w-20')
    })

    it('should have flex column layout', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('flex')
      expect(sidebar?.className).toContain('flex-col')
    })
  })

  describe('styling and colors', () => {
    it('should render as a glass (blurred, translucent) panel', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('glass-panel')
      expect(sidebar?.className).toMatch(/backdrop-blur/)
    })

  })

  describe('no redundant profile card', () => {
    it('should not render a profile summary block - identity already lives in the Navbar', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      expect(container.querySelector('.sidebar-profile')).not.toBeInTheDocument()
    })
  })

  describe('career domain sections', () => {
    it('should render all 5 domains directly - no outer "Carrera" wrapper to expand first', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Identidad Profesional')
      expect(screen.queryByText('Carrera')).not.toBeInTheDocument()
      expect(screen.getByText('Operativa de Búsqueda')).toBeInTheDocument()
      expect(screen.getByText('Presencia Digital')).toBeInTheDocument()
      expect(screen.getByText('Networking')).toBeInTheDocument()
      expect(screen.getByText('Soporte')).toBeInTheDocument()
    })

    it('should not expose a domain resource link until that domain is expanded', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Operativa de Búsqueda')
      expect(screen.queryByText('Vacantes')).not.toBeInTheDocument()
    })

    it('should expand a domain to reveal its resource links pointing at /career/:resourceKey', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Operativa de Búsqueda')
      fireEvent.click(screen.getByText('Operativa de Búsqueda'))

      const vacanciesLink = screen.getByRole('link', { name: /Vacantes/ })
      expect(vacanciesLink).toHaveAttribute('href', '/career/vacancies')
      expect(vacanciesLink.querySelector('svg')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Descubrir vacantes' })).toHaveAttribute(
        'href',
        '/job-discovery'
      )
    })

    it('shows a record-count badge after the name of table subsections, not singletons', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Identidad Profesional')
      fireEvent.click(screen.getByText('Identidad Profesional'))

      const historyLink = await screen.findByRole('link', { name: /Historial Laboral/ })
      await waitFor(() => expect(historyLink).toHaveAccessibleName('Historial Laboral, 4 registros'))
      expect(historyLink.querySelector('svg')).toBeInTheDocument()

      const profileLink = screen.getByRole('link', { name: 'Datos personales' })
      expect(profileLink.querySelector('svg')).toBeInTheDocument()
      expect(profileLink).not.toHaveAccessibleName(/registros/)
    })

    it('should include LinkedIn inside the "Presencia Digital" domain, not as a top-level item', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Presencia Digital')
      expect(screen.queryByRole('link', { name: /LinkedIn/i })).not.toBeInTheDocument()

      fireEvent.click(screen.getByText('Presencia Digital'))
      expect(screen.getByRole('link', { name: 'LinkedIn · Publicar' })).toHaveAttribute('href', '/linkedin')
    })

    it('should collapse the previously expanded domain when a different one is opened (at most one at a time)', async () => {
      renderSidebar(true, mockOnToggle)
      await screen.findByText('Operativa de Búsqueda')
      fireEvent.click(screen.getByText('Operativa de Búsqueda'))
      expect(screen.getByText('Vacantes')).toBeInTheDocument()

      fireEvent.click(screen.getByText('Presencia Digital'))
      expect(screen.queryByText('Vacantes')).not.toBeInTheDocument()
      expect(screen.getByText('Publicaciones')).toBeInTheDocument()
    })

    it('should expand the sidebar itself when a domain icon is clicked while collapsed', async () => {
      renderSidebar(false, mockOnToggle)
      await screen.findByTitle('Identidad Profesional')
      fireEvent.click(screen.getByTitle('Identidad Profesional'))
      expect(mockOnToggle).toHaveBeenCalled()
    })
  })
})
