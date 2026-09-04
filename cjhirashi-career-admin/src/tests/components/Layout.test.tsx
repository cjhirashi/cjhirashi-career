import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../utils'
import { MemoryRouter } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { useAdminSections } from '@/hooks/useAdminSections'
import type { AdminSection } from '@/types/adminSections'

vi.mock('@/hooks/useAdminSections')
vi.mock('@/hooks/useAuth', () => ({ useAuth: () => ({ logout: vi.fn() }) }))
vi.mock('@/components/Sidebar', () => ({ Sidebar: () => <div data-testid="left-sidebar" /> }))
vi.mock('@/components/Navbar', () => ({ Navbar: () => <div data-testid="navbar" /> }))
vi.mock('@/components/SidebarRight', () => ({
  SidebarRight: () => <aside aria-label="Panel de asistencia" />,
}))

const mockedSections = vi.mocked(useAdminSections)

const section = (over: Partial<AdminSection>): AdminSection => ({
  id: 'sec-1',
  system_name: 'dashboard',
  label: 'Dashboard',
  path: '/dashboard',
  section_type: 'metrics',
  group: '',
  resource_key: null,
  related_tools: [],
  default_agent_profile_id: null,
  agent_profile_id: null,
  agent_label: null,
  agent_is_default: true,
  sidebar_has_chat: false,
  sidebar_has_instructions: false,
  view_count: 1,
  views: [
    { key: 'main', label: 'Principal', description: '', sidebar_title: 'Dashboard', sidebar_body: '', is_default: false },
  ],
  ...over,
})

const renderAt = (pathname: string) =>
  render(
    <MemoryRouter initialEntries={[pathname]}>
      <Layout>
        <div>work area</div>
      </Layout>
    </MemoryRouter>
  )

const withSections = (rows: AdminSection[]) =>
  mockedSections.mockReturnValue({ data: rows } as unknown as ReturnType<typeof useAdminSections>)

describe('Layout · right sidebar visibility (RF-011)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // El panel arranca colapsado a un botón salvo en viewport xl (jsdom = 1024px),
  // así que "hay sidebar derecho" se comprueba por el botón "Mostrar panel".

  it('renders neither the panel nor its toggle when the section has no chat and no instructions', () => {
    withSections([section({ sidebar_has_chat: false, sidebar_has_instructions: false })])
    renderAt('/dashboard')
    expect(screen.queryByLabelText('Panel de asistencia')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Mostrar panel de asistencia')).not.toBeInTheDocument()
  })

  it('offers the right panel when the section has a contextual chat agent', () => {
    withSections([section({ sidebar_has_chat: true, agent_profile_id: 'agent_configuration' })])
    renderAt('/dashboard')
    expect(screen.getByLabelText('Mostrar panel de asistencia')).toBeInTheDocument()
  })

  it('offers the right panel on routes that match no catalogued section', () => {
    withSections([])
    renderAt('/some/unmapped/route')
    expect(screen.getByLabelText('Mostrar panel de asistencia')).toBeInTheDocument()
  })
})
