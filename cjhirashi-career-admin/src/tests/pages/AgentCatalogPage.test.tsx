import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor, fireEvent, within } from '../utils'
import { AgentCatalogPage } from '@/pages/AgentCatalogPage'
import { bedrockApi } from '@/api/bedrock'
import { adminNavTreeApi } from '@/api/adminSections'
import { BedrockAgentCatalogItem } from '@/types/bedrock'
import { NavTreeResponse } from '@/types/adminSections'

vi.mock('@/api/bedrock')
vi.mock('@/api/adminSections')
vi.mock('@/api/files', () => ({
  filesApi: {
    list: vi.fn().mockResolvedValue([]),
    upload: vi.fn(),
    setVisibility: vi.fn(),
    getDownloadUrl: vi.fn(),
  },
}))

const mockedApi = vi.mocked(bedrockApi)
const mockedNavTree = vi.mocked(adminNavTreeApi)

const catalogFields = {
  views: [
    {
      id: 'vw-30',
      key: 'list',
      label: 'Plantillas PDF',
      section_id: 's1-40',
      section_system_name: 'pdf-templates',
      section_path: '/agent/pdf-templates',
      data_source: 'crud',
      resource_key: 'pdf-output-templates',
    },
  ],
  delegation_targets: [{ id: 'agent_pdf_render', label: 'Renderizado PDF', level: 3 }],
  delegation_target_ids: ['agent_pdf_render'],
  default_delegation_target_ids: ['agent_pdf_render', 'agent_changelog'],
  allowed_delegation_ids: ['agent_pdf_render', 'agent_changelog'],
  delegation_is_default: true,
}

const sampleAgent: BedrockAgentCatalogItem = {
  id: 'agent-8',
  system_name: 'agent_pdf_design',
  profile_id: 'agent_pdf_design',
  label: 'Diseño PDF',
  level: 2,
  user_facing: true,
  can_delegate: true,
  write_enabled: true,
  domain_keys: ['document_output'],
  resource_keys: ['pdf-output-templates', 'pdf-template-styles'],
  default_model_id: 'us.anthropic.claude-sonnet-4-5-20250929-v1:0',
  tools: ['pdf_style', 'pdf_template', 'search_knowledge_base', 'delegate_to_specialist'],
  has_own_memory: true,
  default_suffix: 'Eres PDF Maker',
  override_suffix: null,
  effective_suffix: 'Eres PDF Maker',
  prompt_is_default: true,
  methodology_count: 1,
  assigned_methodologies: [
    { id: 'opm-1', title: 'Plantillas PDF', section: 'Diseño PDF', shared: false, assigned: true },
    { id: 'opm-2', title: 'Otra', section: null, shared: true, assigned: true },
  ],
  methodologies: [
    { id: 'opm-1', title: 'Plantillas PDF', section: 'Diseño PDF', shared: false, assigned: true },
    { id: 'opm-2', title: 'Otra', section: null, shared: true, assigned: true },
  ],
  conversation_count: 2,
  ...catalogFields,
}

const l3Agent: BedrockAgentCatalogItem = {
  ...sampleAgent,
  id: 'agent-9',
  system_name: 'agent_pdf_render',
  profile_id: 'agent_pdf_render',
  label: 'Renderizado PDF',
  level: 3,
  user_facing: false,
  can_delegate: false,
  has_own_memory: false,
  resource_keys: ['cv-versions', 'cover-letter-versions'],
  tools: ['generate_pdf', 'render_record_pdf'],
  methodology_count: 0,
  assigned_methodologies: [],
  conversation_count: 0,
  views: [],
  delegation_targets: [],
  delegation_target_ids: [],
  default_delegation_target_ids: [],
  allowed_delegation_ids: [],
}

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/settings/agents/:profileId?" element={<AgentCatalogPage />} />
      </Routes>
    </MemoryRouter>
  )

describe('AgentCatalogPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.listAgentCatalog.mockResolvedValue([sampleAgent, l3Agent])
    mockedApi.getAgentCatalogItem.mockResolvedValue(sampleAgent)
    mockedApi.getAgentMemory.mockResolvedValue({
      has_own_memory: true,
      conversation_count: 2,
      notes: [{ id: '11', text: 'Usar paleta cyan' }],
    })
    mockedApi.listConversations.mockResolvedValue([])
    const navTree: NavTreeResponse = {
      groups: [
        {
          id: 'grp-8',
          system_name: 'settings',
          name: 'Settings',
          sort_order: 90,
          sections: [
            {
              id: 's1-16',
              level: 1,
              system_name: 'settings-agents',
              label: 'Catálogo de Agentes',
              path: '/settings/agents',
              section_type: 'table',
              sort_order: 10,
              origin: 'code',
              has_layout: true,
              view_count: 3,
              children: [],
              views: [
                {
                  id: 'vw-1',
                  key: 'list',
                  label: 'Lista',
                  sort_order: 0,
                  data_source: 'crud',
                  resource_key: null,
                  has_controls_window: false,
                  tool_names: [],
                  responsible_agent_profile_id: 'agent_orchestrator',
                  has_instructions: true,
                  chat_enabled: true,
                },
                {
                  id: 'vw-2',
                  key: 'view',
                  label: 'Vista',
                  sort_order: 1,
                  data_source: 'crud',
                  resource_key: null,
                  has_controls_window: false,
                  tool_names: [],
                  responsible_agent_profile_id: 'agent_orchestrator',
                  has_instructions: true,
                  chat_enabled: true,
                },
                {
                  id: 'vw-3',
                  key: 'edit',
                  label: 'Edición',
                  sort_order: 2,
                  data_source: 'crud',
                  resource_key: null,
                  has_controls_window: false,
                  tool_names: [],
                  responsible_agent_profile_id: 'agent_orchestrator',
                  has_instructions: true,
                  chat_enabled: true,
                },
              ],
            },
          ],
        },
      ],
      generated_at: '2026-08-28T12:00:00Z',
    }
    mockedNavTree.get.mockResolvedValue(navTree)
  })

  it('lists agents with table-section chrome and no create action', async () => {
    renderAt('/settings/agents')
    await waitFor(() => expect(screen.getByText('Diseño PDF')).toBeInTheDocument())
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Vista' }).tagName).not.toBe('BUTTON')
    expect(screen.getByRole('tab', { name: 'Edición' }).tagName).not.toBe('BUTTON')
    expect(screen.getByPlaceholderText(/buscar en catálogo de agentes/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Nuevo' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Eliminar' })).not.toBeInTheDocument()
    expect(screen.getByText('agent-8')).toBeInTheDocument()
    expect(screen.getByText('agent_pdf_design')).toBeInTheDocument()
    expect(screen.getByText('Renderizado PDF')).toBeInTheDocument()
    expect(screen.getByText('2 chats')).toBeInTheDocument()
  })

  it('opens Vista from a row and Edición from the edit button', async () => {
    renderAt('/settings/agents')
    await waitFor(() => expect(screen.getByText('Diseño PDF')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Diseño PDF'))
    await waitFor(() => expect(screen.getByRole('tab', { name: 'Vista' })).toHaveAttribute('aria-selected', 'true'))
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Catálogo de Agentes')
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('agent-8')
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Diseño PDF')
    expect(screen.getByText('pdf_style')).toBeInTheDocument()
    expect(screen.getByText('Foto')).toBeInTheDocument()
    expect(screen.queryByLabelText('Prompt del especialista')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Edición' }))
    expect(screen.getByRole('tab', { name: 'Vista' })).toHaveAttribute('aria-selected', 'true')

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    await waitFor(() => expect(screen.getByRole('tab', { name: 'Edición' })).toHaveAttribute('aria-selected', 'true'))
    expect(screen.getAllByText('Editable').length).toBeGreaterThan(0)
    await waitFor(() =>
      expect(screen.getByLabelText('Prompt del especialista')).toHaveValue('Eres PDF Maker')
    )
    expect(screen.getByRole('button', { name: /guardar prompt/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /guardar metodologías/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /guardar delegación/i })).toBeInTheDocument()
    expect(screen.getByText('Vistas que gestiona')).toBeInTheDocument()
    expect(screen.getByText('pdf-templates · Plantillas PDF')).toBeInTheDocument()
    expect(screen.getByText('Usar paleta cyan')).toBeInTheDocument()
    expect(screen.getByText(/elige una imagen del bucket/i)).toBeInTheDocument()
  })

  it('tells L3 agents they have no own memory', async () => {
    mockedApi.getAgentCatalogItem.mockResolvedValue(l3Agent)
    mockedApi.getAgentMemory.mockResolvedValue({
      has_own_memory: false,
      conversation_count: 0,
      notes: [],
    })
    renderAt('/settings/agents/agent-9')
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Renderizado PDF')
    )
    expect(screen.getByText(/no tienen chat ni memoria propia/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    await waitFor(() => expect(screen.getByRole('tab', { name: 'Edición' })).toHaveAttribute('aria-selected', 'true'))
    expect(screen.getByText(/no tienen chat ni memoria propia/i)).toBeInTheDocument()
    expect(screen.queryByLabelText('Nueva nota de memoria')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /guardar delegación/i })).not.toBeInTheDocument()
  })

  it('saves a prompt override from Edición', async () => {
    mockedApi.updateAgentProfilePrompt.mockResolvedValue({
      profile_id: 'agent_pdf_design',
      label: 'Diseño PDF',
      default_suffix: 'Eres PDF Maker',
      override_suffix: 'Custom',
      effective_suffix: 'Custom',
      is_default: false,
    })
    renderAt('/settings/agents/agent-8')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    await waitFor(() => expect(screen.getByLabelText('Prompt del especialista')).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText('Prompt del especialista'), { target: { value: 'Custom' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar prompt/i }))
    await waitFor(() =>
      expect(mockedApi.updateAgentProfilePrompt).toHaveBeenCalledWith('agent_pdf_design', 'Custom')
    )
  })

  it('L2 delegation multiselect only offers lower-level (L3) targets, never L1/L2', async () => {
    // sampleAgent is level 2 and its allowed_delegation_ids are all L3
    // (agent_pdf_render, agent_changelog). Add one more L3 id to be sure the
    // filter is by `allowed_delegation_ids` and not the default selection.
    mockedApi.getAgentCatalogItem.mockResolvedValue({
      ...sampleAgent,
      allowed_delegation_ids: ['agent_pdf_render', 'agent_changelog', 'agent_web_search'],
      // default selection intentionally references a broader set; it must NOT
      // leak into the option universe.
      default_delegation_target_ids: ['agent_pdf_render'],
    })
    renderAt('/settings/agents/agent-8')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /guardar delegación/i })).toBeInTheDocument()
    )

    const combo = screen.getByRole('combobox', { name: 'Agentes destino de delegación' })
    fireEvent.click(combo)

    const listbox = await screen.findByRole('listbox', { name: 'Agentes destino de delegación' })
    const optionLabels = within(listbox)
      .getAllByRole('option')
      .map((el) => (el.textContent ?? '').trim())

    expect(optionLabels.length).toBeGreaterThan(0)
    // no option belongs to L1 or L2
    expect(optionLabels.some((t) => /\(L[12]\)$/.test(t))).toBe(false)
    expect(optionLabels.every((t) => /\(L3\)$/.test(t))).toBe(true)
    // a known L2 target ("Identidad Profesional (L2)") is not selectable
    expect(optionLabels.some((t) => t.includes('Identidad Profesional'))).toBe(false)
  })

  it('does not blow up when allowed_delegation_ids is empty/undefined', async () => {
    mockedApi.getAgentCatalogItem.mockResolvedValue({
      ...sampleAgent,
      allowed_delegation_ids: undefined as unknown as string[],
    })
    renderAt('/settings/agents/agent-8')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /guardar delegación/i })).toBeInTheDocument()
    )

    fireEvent.click(screen.getByRole('combobox', { name: 'Agentes destino de delegación' }))
    const listbox = await screen.findByRole('listbox', { name: 'Agentes destino de delegación' })
    expect(within(listbox).queryAllByRole('option')).toHaveLength(0)
    expect(within(listbox).getByText('No hay opciones')).toBeInTheDocument()
  })

  it('filters the list from the search box', async () => {
    renderAt('/settings/agents')
    await waitFor(() => expect(screen.getByText('Diseño PDF')).toBeInTheDocument())
    fireEvent.change(screen.getByPlaceholderText(/buscar en catálogo de agentes/i), {
      target: { value: 'Renderizado' },
    })
    await waitFor(() => expect(screen.queryByText('Diseño PDF')).not.toBeInTheDocument())
    expect(screen.getByText('Renderizado PDF')).toBeInTheDocument()
  })
})
