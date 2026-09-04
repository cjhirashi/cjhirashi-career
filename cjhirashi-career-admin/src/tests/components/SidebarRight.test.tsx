import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '../utils'
import { MemoryRouter } from 'react-router-dom'
import { SidebarRight } from '@/components/SidebarRight'
import { useAdminSections } from '@/hooks/useAdminSections'
import type { AdminSection } from '@/types/adminSections'

vi.mock('@/hooks/useAdminSections')
const mockedSections = vi.mocked(useAdminSections)

const section = (over: Partial<AdminSection> = {}): AdminSection => ({
  id: 'sec-1',
  system_name: 'dashboard',
  label: 'Dashboard',
  path: '/dashboard',
  section_type: 'metrics',
  group: 'Métricas',
  resource_key: null,
  related_tools: [],
  default_agent_profile_id: 'agent_configuration',
  agent_profile_id: 'agent_configuration',
  agent_label: 'Configuración',
  agent_is_default: true,
  sidebar_has_chat: true,
  sidebar_has_instructions: true,
  view_count: 1,
  views: [
    {
      key: 'main',
      label: 'Principal',
      description: '',
      sidebar_title: 'Dashboard',
      sidebar_body: 'Resumen **general** de tu actividad.',
      is_default: true,
    },
  ],
  ...over,
})

const withSections = (rows: AdminSection[] | undefined) =>
  mockedSections.mockReturnValue({ data: rows } as unknown as ReturnType<typeof useAdminSections>)

const renderAt = (pathname: string, onClose = vi.fn()) =>
  render(
    <MemoryRouter initialEntries={[pathname]}>
      <SidebarRight onClose={onClose} />
    </MemoryRouter>
  )

describe('SidebarRight', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    withSections(undefined) // rutas no catalogadas → comportamiento anterior
  })

  it('defaults to the "Instrucciones" tab', () => {
    renderAt('/dashboard')
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('switches to the chat window when the chat tab is pressed', () => {
    renderAt('/dashboard')
    fireEvent.click(screen.getByTitle('Chat del asistente'))
    expect(screen.getByPlaceholderText('Escribe un mensaje...')).toBeInTheDocument()
  })

  it('calls onClose when the hide button is clicked', () => {
    const onClose = vi.fn()
    renderAt('/dashboard', onClose)
    fireEvent.click(screen.getByLabelText('Ocultar panel'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('derives instructions for a career-domain resource on an uncatalogued route', () => {
    renderAt('/career/vacancies')
    expect(screen.getByText('Vacantes')).toBeInTheDocument()
  })

  // feature 001 ------------------------------------------------------------

  it('renders section instructions as Markdown (RF-008)', () => {
    withSections([section()])
    renderAt('/dashboard')
    const strong = screen.getByText('general')
    expect(strong.tagName).toBe('STRONG')
  })

  it('hides the instructions tab when the view has no instructions (RF-009)', () => {
    withSections([
      section({
        sidebar_has_instructions: false,
        views: [
          { key: 'main', label: 'Principal', description: '', sidebar_title: 'Dashboard', sidebar_body: '', is_default: false },
        ],
      }),
    ])
    renderAt('/dashboard')
    expect(screen.queryByTitle('Instrucciones de la pantalla')).not.toBeInTheDocument()
    // el chat sigue disponible
    expect(screen.getByPlaceholderText('Escribe un mensaje...')).toBeInTheDocument()
  })

  it('hides the chat tab when the section has no L2 agent (RF-010)', () => {
    withSections([section({ agent_profile_id: null, sidebar_has_chat: false })])
    renderAt('/dashboard')
    expect(screen.queryByTitle('Chat del asistente')).not.toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('does not execute embedded HTML in instructions (RF-019)', () => {
    withSections([
      section({
        views: [
          {
            key: 'main',
            label: 'Principal',
            description: '',
            sidebar_title: 'Dashboard',
            sidebar_body: 'texto <img src=x onerror="window.__pwned=1"> más',
            is_default: false,
          },
        ],
      }),
    ])
    renderAt('/dashboard')
    expect((window as unknown as { __pwned?: number }).__pwned).toBeUndefined()
    expect(document.querySelector('img[onerror]')).toBeNull()
  })
})
