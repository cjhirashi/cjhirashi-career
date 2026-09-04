import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor, fireEvent } from '../utils'
import { AdminSectionDetailPage, AdminSectionsPage } from '@/pages/AdminSectionsPage'
import { adminSectionsApi } from '@/api/adminSections'
import { AdminSection } from '@/types/adminSections'

vi.mock('@/api/adminSections')

const mockedApi = vi.mocked(adminSectionsApi)

const sample: AdminSection = {
  id: 'sec-6',
  system_name: 'linkedin-publish',
  label: 'LinkedIn · Publicar',
  path: '/linkedin',
  section_type: 'functional',
  group: 'Presencia Digital',
  resource_key: null,
  related_tools: ['get_linkedin_status'],
  default_agent_profile_id: 'agent_digital_presence',
  agent_profile_id: 'agent_digital_presence',
  agent_label: 'Presencia Digital',
  agent_is_default: true,
  sidebar_has_chat: true,
  sidebar_has_instructions: true,
  view_count: 1,
  views: [
    {
      key: 'main',
      label: 'Principal',
      description: 'Publicación vía API.',
      sidebar_title: 'LinkedIn · Publicar',
      sidebar_body: 'Conecta **OAuth** y publica.',
      is_default: true,
    },
  ],
}

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/settings/sections" element={<AdminSectionsPage />} />
        <Route path="/settings/sections/:sectionId" element={<AdminSectionDetailPage />} />
      </Routes>
    </MemoryRouter>
  )

describe('AdminSectionsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.list.mockResolvedValue([sample])
    mockedApi.get.mockResolvedValue(sample)
  })

  it('lists sections with type, owner and view count', async () => {
    renderAt('/settings/sections')
    await waitFor(() => expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument())
    expect(screen.getByText('funcional')).toBeInTheDocument()
    expect(screen.getByText('Presencia Digital', { selector: 'span' })).toBeTruthy()
    expect(screen.getByText('sec-6')).toBeInTheDocument()
    expect(screen.getByText('linkedin-publish')).toBeInTheDocument()
  })

  it('renders sidebar instructions as Markdown in the record view (RF-008)', async () => {
    renderAt('/settings/sections/sec-6')
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Secciones del Admin')
    )
    const strong = screen.getByText('OAuth')
    expect(strong.tagName).toBe('STRONG')
  })

  it('has no section-level "Descripción" field in edit mode (RF-013)', async () => {
    renderAt('/settings/sections/sec-6')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    expect(screen.queryByLabelText('Descripción de la sección')).not.toBeInTheDocument()
  })

  it('shows the contextual-chat agent selector, not the old "dominio" field (RF-014)', async () => {
    renderAt('/settings/sections/sec-6')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    expect(screen.getByLabelText('Agente del chat contextual')).toBeInTheDocument()
    expect(screen.queryByLabelText('Agente con dominio')).not.toBeInTheDocument()
    expect(screen.queryByText(/Chat contextual:/)).not.toBeInTheDocument()
  })

  it('saves the sidebar_body override per view', async () => {
    mockedApi.update.mockResolvedValue(sample)
    renderAt('/settings/sections/sec-6')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText(/Instrucciones del sidebar derecho/i), {
      target: { value: '## Nuevas instrucciones' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar' }))
    await waitFor(() =>
      expect(mockedApi.update).toHaveBeenCalledWith(
        'sec-6',
        expect.objectContaining({
          views: expect.objectContaining({
            main: expect.objectContaining({ sidebar_body: '## Nuevas instrucciones' }),
          }),
        })
      )
    )
    expect(mockedApi.update.mock.calls[0][1]).not.toHaveProperty('description')
  })
})
