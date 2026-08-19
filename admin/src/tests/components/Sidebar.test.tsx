import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '../utils'
import { Sidebar } from '@/components/Sidebar'
import { BrowserRouter } from 'react-router-dom'

// Mock useLocation to control current path
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useLocation: () => ({ pathname: '/dashboard' }),
  }
})

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
  })

  describe('rendering', () => {
    it('should render sidebar element', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar).toBeInTheDocument()
    })

    it('should display the static menu items when open', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Métricas')).toBeInTheDocument()
      expect(screen.getByText('Archivos')).toBeInTheDocument()
    })

    it('should not render legacy (pre-career-domain) menu items anymore', () => {
      renderSidebar(true, mockOnToggle)
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
    it('should render the static top-level links', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByRole('link', { name: /Dashboard/i })).toHaveAttribute('href', '/dashboard')
      expect(screen.getByRole('link', { name: /Métricas/i })).toHaveAttribute('href', '/metrics')
      expect(screen.getByRole('link', { name: /Archivos/i })).toHaveAttribute('href', '/files')
    })

    it('should render a Lucide (svg) icon for each static link', () => {
      renderSidebar(true, mockOnToggle)
      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      expect(dashboardLink.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('active state styling', () => {
    it('should highlight the active menu item', () => {
      renderSidebar(true, mockOnToggle)
      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      expect(dashboardLink.className).toContain('is-active')
      expect(dashboardLink).toHaveAttribute('aria-current', 'page')
    })

    it('should not highlight inactive menu items', () => {
      renderSidebar(true, mockOnToggle)
      const metricsLink = screen.getByRole('link', { name: /Métricas/i })
      expect(metricsLink.className).not.toContain('is-active')
      expect(metricsLink).not.toHaveAttribute('aria-current')
    })

    it('should use the shared sidebar-item styling for every link', () => {
      renderSidebar(true, mockOnToggle)
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
    it('should render all 5 domains directly - no outer "Carrera" wrapper to expand first', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.queryByText('Carrera')).not.toBeInTheDocument()
      expect(screen.getByText('Identidad Profesional')).toBeInTheDocument()
      expect(screen.getByText('Operativa de Búsqueda')).toBeInTheDocument()
      expect(screen.getByText('Presencia Digital')).toBeInTheDocument()
      expect(screen.getByText('Networking')).toBeInTheDocument()
      expect(screen.getByText('Soporte')).toBeInTheDocument()
    })

    it('should not expose a domain resource link until that domain is expanded', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.queryByText('Vacantes')).not.toBeInTheDocument()
    })

    it('should expand a domain to reveal its resource links pointing at /career/:resourceKey', () => {
      renderSidebar(true, mockOnToggle)
      fireEvent.click(screen.getByText('Operativa de Búsqueda'))

      const vacanciesLink = screen.getByRole('link', { name: 'Vacantes' })
      expect(vacanciesLink).toHaveAttribute('href', '/career/vacancies')
    })

    it('should collapse the previously expanded domain when a different one is opened (at most one at a time)', () => {
      renderSidebar(true, mockOnToggle)
      fireEvent.click(screen.getByText('Operativa de Búsqueda'))
      expect(screen.getByText('Vacantes')).toBeInTheDocument()

      fireEvent.click(screen.getByText('Presencia Digital'))
      expect(screen.queryByText('Vacantes')).not.toBeInTheDocument()
      expect(screen.getByText('Publicaciones')).toBeInTheDocument()
    })

    it('should expand the sidebar itself when a domain icon is clicked while collapsed', () => {
      renderSidebar(false, mockOnToggle)
      fireEvent.click(screen.getByTitle('Identidad Profesional'))
      expect(mockOnToggle).toHaveBeenCalled()
    })
  })
})
