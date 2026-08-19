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

    it('should display all menu items when open', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Identity')).toBeInTheDocument()
      expect(screen.getByText('Competencies')).toBeInTheDocument()
      expect(screen.getByText('Evidence')).toBeInTheDocument()
      expect(screen.getByText('Job Strategies')).toBeInTheDocument()
      expect(screen.getByText('Networking')).toBeInTheDocument()
      expect(screen.getByText('Interviews')).toBeInTheDocument()
      expect(screen.getByText('Metrics')).toBeInTheDocument()
    })

    it('should render portfolio title when open', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByText('Portfolio')).toBeInTheDocument()
    })

    it('should not show menu labels when closed', () => {
      renderSidebar(false, mockOnToggle)
      // Menu items should exist but labels shouldn't be visible
      const dashboardLabel = screen.queryByText('Dashboard')
      expect(dashboardLabel).not.toBeInTheDocument()
    })

    it('should not show portfolio title when closed', () => {
      renderSidebar(false, mockOnToggle)
      expect(screen.queryByText('Portfolio')).not.toBeInTheDocument()
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
      expect(screen.getByTitle('Collapse')).toBeInTheDocument()
    })

    it('should call onToggle when button clicked', () => {
      renderSidebar(true, mockOnToggle)
      const toggleButton = screen.getByTitle('Collapse')
      fireEvent.click(toggleButton)
      expect(mockOnToggle).toHaveBeenCalled()
    })

    it('should have correct title when open', () => {
      renderSidebar(true, mockOnToggle)
      const toggleButton = screen.getByTitle('Collapse')
      expect(toggleButton).toHaveAttribute('title', 'Collapse')
    })

    it('should have correct title when closed', () => {
      renderSidebar(false, mockOnToggle)
      const toggleButton = screen.getByTitle('Expand')
      expect(toggleButton).toHaveAttribute('title', 'Expand')
    })
  })

  describe('menu items and links', () => {
    it('should render all menu items as links', () => {
      renderSidebar(true, mockOnToggle)
      const links = screen.getAllByRole('link')
      expect(links.length).toBe(8)
    })

    it('should have correct href for dashboard link', () => {
      renderSidebar(true, mockOnToggle)
      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      expect(dashboardLink).toHaveAttribute('href', '/dashboard')
    })

    it('should have correct href for identity link', () => {
      renderSidebar(true, mockOnToggle)
      const identityLink = screen.getByRole('link', { name: /Identity/i })
      expect(identityLink).toHaveAttribute('href', '/identity')
    })

    it('should have correct href for competencies link', () => {
      renderSidebar(true, mockOnToggle)
      const compLink = screen.getByRole('link', { name: /Competencies/i })
      expect(compLink).toHaveAttribute('href', '/competencies')
    })

    it('should have correct href for job strategies link', () => {
      renderSidebar(true, mockOnToggle)
      const jobLink = screen.getByRole('link', { name: /Job Strategies/i })
      expect(jobLink).toHaveAttribute('href', '/job-strategies')
    })

    it('should have all links with icons', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const icons = container.querySelectorAll('span.text-xl')
      expect(icons.length).toBeGreaterThan(0)
    })
  })

  describe('active state styling', () => {
    it('should highlight active menu item', () => {
      renderSidebar(true, mockOnToggle)
      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      expect(dashboardLink.className).toContain('is-active')
      expect(dashboardLink).toHaveAttribute('aria-current', 'page')
    })

    it('should not highlight inactive menu items', () => {
      renderSidebar(true, mockOnToggle)
      const identityLink = screen.getByRole('link', { name: /Identity/i })
      expect(identityLink.className).not.toContain('is-active')
      expect(identityLink).not.toHaveAttribute('aria-current')
    })

    it('should use the shared sidebar-item styling for every link', () => {
      renderSidebar(true, mockOnToggle)
      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      const identityLink = screen.getByRole('link', { name: /Identity/i })
      expect(dashboardLink.className).toContain('sidebar-item')
      expect(identityLink.className).toContain('sidebar-item')
    })
  })

  describe('sizing and layout', () => {
    it('should have wide width when open', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('w-64')
    })

    it('should have narrow width when closed', () => {
      const { container } = renderSidebar(false, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('w-20')
    })

    it('should have flex column layout', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('flex')
      expect(sidebar?.className).toContain('flex-col')
    })

    it('should have smooth transition', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('transition-all')
      expect(sidebar?.className).toContain('duration-300')
    })
  })

  describe('styling and colors', () => {
    it('should render as a glass (blurred, translucent) panel', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('glass-panel')
      expect(sidebar?.className).toMatch(/backdrop-blur/)
      expect(sidebar?.className).toContain('text-text')
    })

    it('should have primary (cyan) title color when open', () => {
      renderSidebar(true, mockOnToggle)
      const title = screen.getByText('Portfolio')
      expect(title.className).toContain('text-primary')
    })

    it('should have a themed glass border', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const sidebar = container.querySelector('aside')
      expect(sidebar?.className).toContain('border-border')
    })

    it('should use the shared sidebar-item class (hover handled in CSS) on inactive items', () => {
      renderSidebar(true, mockOnToggle)
      const identityLink = screen.getByRole('link', { name: /Identity/i })
      expect(identityLink.className).toContain('sidebar-item')
    })
  })

  describe('profile footer', () => {
    it('should render a profile summary block when open', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      expect(container.querySelector('.sidebar-profile')).toBeInTheDocument()
    })

    it('should fall back to "U" avatar initial when there is no user', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByText('U')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('should have proper title for toggle button when open', () => {
      renderSidebar(true, mockOnToggle)
      const button = screen.getByTitle('Collapse')
      expect(button.getAttribute('title')).toBe('Collapse')
    })

    it('should have proper title for toggle button when closed', () => {
      renderSidebar(false, mockOnToggle)
      const button = screen.getByTitle('Expand')
      expect(button.getAttribute('title')).toBe('Expand')
    })

    it('should show titles on links when closed', () => {
      const { container } = renderSidebar(false, mockOnToggle)
      const links = container.querySelectorAll('a[title]')
      expect(links.length).toBeGreaterThan(0)
    })

    it('should not have redundant titles when open', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const links = container.querySelectorAll('a:not([title])')
      expect(links.length).toBeGreaterThan(0)
    })
  })

  describe('menu organization', () => {
    it('should have navigation section', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const nav = container.querySelector('nav')
      expect(nav).toBeInTheDocument()
    })

    it('should have header section', () => {
      const { container } = renderSidebar(true, mockOnToggle)
      const divs = container.querySelectorAll('div')
      expect(divs.length).toBeGreaterThan(0)
    })

    it('should have footer section with version', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByText('v0.1.0')).toBeInTheDocument()
    })
  })

  describe('career navigation section', () => {
    it('should render a collapsed "Carrera" toggle without exposing resource links by default', () => {
      renderSidebar(true, mockOnToggle)
      expect(screen.getByText('Carrera')).toBeInTheDocument()
      expect(screen.queryByText('Vacantes')).not.toBeInTheDocument()
      // Still only the 8 static menu links until the section is expanded.
      expect(screen.getAllByRole('link').length).toBe(8)
    })

    it('should expand to show the 5 domain groups when clicked', () => {
      renderSidebar(true, mockOnToggle)
      fireEvent.click(screen.getByText('Carrera'))
      expect(screen.getByText('Identidad Profesional')).toBeInTheDocument()
      expect(screen.getByText('Operativa de Búsqueda')).toBeInTheDocument()
      expect(screen.getByText('Presencia Digital')).toBeInTheDocument()
      // "Networking" is ambiguous with the static top-level menu link, so we
      // disambiguate the domain group header via its button role.
      expect(screen.getByRole('button', { name: /Networking/i })).toBeInTheDocument()
      expect(screen.getByText('Soporte')).toBeInTheDocument()
    })

    it('should expand a domain to reveal its resource links pointing at /career/:resourceKey', () => {
      renderSidebar(true, mockOnToggle)
      fireEvent.click(screen.getByText('Carrera'))
      fireEvent.click(screen.getByText('Operativa de Búsqueda'))

      const vacanciesLink = screen.getByRole('link', { name: 'Vacantes' })
      expect(vacanciesLink).toHaveAttribute('href', '/career/vacancies')
    })

    it('should expand the sidebar itself when the "Carrera" icon is clicked while collapsed', () => {
      renderSidebar(false, mockOnToggle)
      const careerToggle = screen.getByTitle('Carrera')
      fireEvent.click(careerToggle)
      expect(mockOnToggle).toHaveBeenCalled()
    })
  })
})
