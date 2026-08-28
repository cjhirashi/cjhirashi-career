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
  default_agent_profile_id: 'agent_linkedin_publishing',
  agent_profile_id: 'agent_linkedin_publishing',
  agent_label: 'Control de publicación LinkedIn',
  chat_agent_profile_id: 'agent_digital_presence',
  agent_is_default: true,
  description: 'Integración API de LinkedIn.',
  description_is_default: true,
  view_count: 1,
  views: [
    {
      key: 'main',
      label: 'Principal',
      description: 'Publicación vía API.',
      sidebar_title: 'LinkedIn · Publicar',
      sidebar_body: 'Conecta OAuth y publica.',
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
    expect(screen.getByText('Control de publicación LinkedIn')).toBeInTheDocument()
    expect(screen.getByText('sec-6')).toBeInTheDocument()
    expect(screen.getByText('linkedin-publish')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/buscar en secciones/i)).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveAttribute('aria-selected', 'true')
  })

  it('edits owner and sidebar instructions', async () => {
    mockedApi.update.mockResolvedValue({
      ...sample,
      description: 'Nueva descripción',
      description_is_default: false,
    })
    renderAt('/settings/sections/sec-6')
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Secciones del Admin')
    )
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('sec-6')
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Descripción de la sección'), {
      target: { value: 'Nueva descripción' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar' }))
    await waitFor(() =>
      expect(mockedApi.update).toHaveBeenCalledWith(
        'sec-6',
        expect.objectContaining({ description: 'Nueva descripción' })
      )
    )
  })
})
