import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor, fireEvent, within } from '../utils'
import { AdminViewDetailPage, AdminViewsPage } from '@/pages/AdminViewsPage'
import { adminViewsApi } from '@/api/adminSections'
import { AdminViewItem } from '@/types/adminSections'

vi.mock('@/api/adminSections')

// jsdom doesn't implement scrollIntoView; ThemedSelect's option-highlight
// effect calls it whenever the popover opens.
Element.prototype.scrollIntoView = vi.fn()

const mockedViews = vi.mocked(adminViewsApi)

const linkedinView: AdminViewItem = {
  id: 'vw-12',
  owner: {
    level: 1,
    section_id: 's1-6',
    section_system_name: 'linkedin-publish',
    section_label: 'LinkedIn · Publicar',
    section_path: '/linkedin',
  },
  key: 'main',
  label: 'Principal',
  sort_order: 0,
  data_source: 'external',
  resource_key: null,
  has_controls_window: false,
  tool_names: ['get_linkedin_status'],
  responsible_agent_profile_id: 'agent_digital_presence',
  responsible_agent_label: 'Presencia Digital',
  responsible_is_l2: true,
  instructions: 'Conecta OAuth y publica.',
  chat_enabled: true,
  instructions_enabled: true,
}

const publicationsView: AdminViewItem = {
  id: 'vw-13',
  owner: {
    level: 1,
    section_id: 's1-7',
    section_system_name: 'career-publications',
    section_label: 'Publicaciones',
    section_path: '/career/publications',
  },
  key: 'list',
  label: 'Lista',
  sort_order: 0,
  data_source: 'crud',
  resource_key: 'publications',
  has_controls_window: false,
  tool_names: [],
  responsible_agent_profile_id: null,
  responsible_agent_label: null,
  responsible_is_l2: false,
  instructions: null,
  chat_enabled: false,
  instructions_enabled: false,
}

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/settings/views" element={<AdminViewsPage />} />
        <Route path="/settings/views/:viewId" element={<AdminViewDetailPage />} />
      </Routes>
    </MemoryRouter>
  )

describe('AdminViewsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedViews.list.mockResolvedValue([linkedinView, publicationsView])
    mockedViews.get.mockResolvedValue(linkedinView)
  })

  // =========================================================================
  // Lista
  // =========================================================================

  it('lists views with their section, origin and responsible agent', async () => {
    renderAt('/settings/views')
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument())
    expect(screen.getByText('Principal')).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Lista' })).toBeInTheDocument()
    expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument()
    expect(screen.getByText('Publicaciones')).toBeInTheDocument()
    expect(screen.getByText('Presencia Digital')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/buscar en vistas/i)).toBeInTheDocument()
  })

  it('shows a placeholder for views without a responsible agent', async () => {
    renderAt('/settings/views')
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument())
    const row = screen.getByRole('cell', { name: 'Lista' }).closest('tr')
    expect(row).not.toBeNull()
    expect(row).toHaveTextContent('—')
  })

  it('filters views by section_id from the query string', async () => {
    renderAt('/settings/views?section_id=s1-6')
    await waitFor(() =>
      expect(mockedViews.list).toHaveBeenCalledWith({ section_id: 's1-6' })
    )
  })

  it('shows an empty state when a filtered section has no views', async () => {
    mockedViews.list.mockResolvedValue([])
    renderAt('/settings/views?section_id=s1-99')
    await waitFor(() =>
      expect(screen.getByText('Esta sección no tiene vistas.')).toBeInTheDocument()
    )
  })

  it('opens a view detail from a row click', async () => {
    renderAt('/settings/views')
    await waitFor(() => expect(screen.getByText('Principal')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Principal'))
    await waitFor(() => expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Vistas'))
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('vw-12')
  })

  // =========================================================================
  // Detalle — vista de solo lectura
  // =========================================================================

  it('shows the view record with owner section, agent and instructions', async () => {
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('vw-12'))
    expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument()
    expect(screen.getByText('Presencia Digital')).toBeInTheDocument()
    expect(screen.getAllByText('Habilitado')).toHaveLength(2)
    expect(screen.getByText('Conecta OAuth y publica.')).toBeInTheDocument()
    expect(screen.getByText('get_linkedin_status')).toBeInTheDocument()
  })

  it('shows the "no agent" placeholder and disabled states for a view without a responsible agent', async () => {
    mockedViews.get.mockResolvedValue(publicationsView)
    renderAt('/settings/views/vw-13')
    await waitFor(() => expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('vw-13'))
    expect(screen.getByText('— Sin agente (chat deshabilitado) —')).toBeInTheDocument()
    expect(screen.getAllByText('Deshabilitado')).toHaveLength(2)
  })

  it('shows an error message when the view fails to load', async () => {
    mockedViews.get.mockRejectedValue(new Error('boom'))
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByText('boom')).toBeInTheDocument())
  })

  // =========================================================================
  // Edición — responsable (restringido a L2) + instrucciones
  // =========================================================================

  it('offers only L2 profiles as responsible agent options', async () => {
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))

    fireEvent.click(screen.getByRole('button', { name: 'Agente responsable del chat contextual' }))
    const listbox = await screen.findByRole('listbox', { name: 'Agente responsable del chat contextual' })

    const optionLabels = within(listbox)
      .getAllByRole('option')
      .map((el) => (el.textContent ?? '').trim())

    expect(optionLabels).toContain('agent_digital_presencePresencia Digital')
    expect(optionLabels).toContain('agent_search_operationsOperativa de Búsqueda')
    // L1 (orquestador) and L3 (e.g. renderizado PDF) must never be offered.
    expect(optionLabels.some((t) => t.includes('Orquestador'))).toBe(false)
    expect(optionLabels.some((t) => t.includes('Renderizado PDF'))).toBe(false)
    expect(
      screen.getByText('Solo perfiles de nivel 2 pueden llevar el chat contextual de una vista.')
    ).toBeInTheDocument()
  })

  it('edits the responsible agent and instructions, then saves the change', async () => {
    mockedViews.update.mockResolvedValue({
      ...linkedinView,
      responsible_agent_profile_id: 'agent_search_operations',
      responsible_agent_label: 'Operativa de Búsqueda',
      instructions: 'Nuevas instrucciones.',
    })
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))

    fireEvent.click(screen.getByRole('button', { name: 'Agente responsable del chat contextual' }))
    fireEvent.click(
      await screen.findByRole('option', { name: 'agent_search_operations Operativa de Búsqueda' })
    )

    fireEvent.change(screen.getByLabelText('Instrucciones de la vista'), {
      target: { value: 'Nuevas instrucciones.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() =>
      expect(mockedViews.update).toHaveBeenCalledWith('vw-12', {
        responsible_agent_profile_id: 'agent_search_operations',
        instructions: 'Nuevas instrucciones.',
      })
    )
    // Saving returns to the read-only view.
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
  })

  it('disables "Actualizar" until something changed', async () => {
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))

    expect(screen.getByRole('button', { name: 'Actualizar' })).toBeDisabled()

    fireEvent.change(screen.getByLabelText('Instrucciones de la vista'), {
      target: { value: 'Algo distinto.' },
    })
    expect(screen.getByRole('button', { name: 'Actualizar' })).not.toBeDisabled()
  })

  it('cancels the edit without saving', async () => {
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Instrucciones de la vista'), {
      target: { value: 'Borrador que no se guarda.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(mockedViews.update).not.toHaveBeenCalled()
    expect(screen.getByText('Conecta OAuth y publica.')).toBeInTheDocument()
  })

  it('clears the responsible agent and instructions from "Quitar responsable e instrucciones"', async () => {
    mockedViews.update.mockResolvedValue({
      ...linkedinView,
      responsible_agent_profile_id: null,
      responsible_agent_label: null,
      instructions: null,
      chat_enabled: false,
      instructions_enabled: false,
    })
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))

    fireEvent.click(screen.getByRole('button', { name: 'Quitar responsable e instrucciones' }))

    await waitFor(() =>
      expect(mockedViews.update).toHaveBeenCalledWith('vw-12', {
        responsible_agent_profile_id: '',
        instructions: '',
      })
    )
  })

  it('disables "Quitar responsable e instrucciones" when the view already has none', async () => {
    mockedViews.get.mockResolvedValue(publicationsView)
    renderAt('/settings/views/vw-13')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))

    expect(
      screen.getByRole('button', { name: 'Quitar responsable e instrucciones' })
    ).toBeDisabled()
  })

  it('shows the mutation error message when saving fails', async () => {
    mockedViews.update.mockRejectedValue(new Error('unknown agent profile'))
    renderAt('/settings/views/vw-12')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Instrucciones de la vista'), {
      target: { value: 'Cambio que falla.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar' }))

    await waitFor(() => expect(screen.getByText('unknown agent profile')).toBeInTheDocument())
  })
})
