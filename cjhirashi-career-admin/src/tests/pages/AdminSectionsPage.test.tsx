import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor, fireEvent } from '../utils'
import { AdminSectionDetailPage, AdminSectionsPage } from '@/pages/AdminSectionsPage'
import { adminNavTreeApi, adminSectionGroupsApi, adminSectionsApi } from '@/api/adminSections'
import { NavTreeResponse, SectionDetail } from '@/types/adminSections'

vi.mock('@/api/adminSections')

const mockedNavTree = vi.mocked(adminNavTreeApi)
const mockedSections = vi.mocked(adminSectionsApi)
const mockedGroups = vi.mocked(adminSectionGroupsApi)

const mainView = {
  id: 'vw-12',
  key: 'main',
  label: 'Principal',
  sort_order: 0,
  data_source: 'external',
  resource_key: null,
  has_controls_window: false,
  tool_names: ['get_linkedin_status'],
  responsible_agent_profile_id: 'agent_digital_presence',
  has_instructions: true,
  chat_enabled: true,
}

const sampleTree: NavTreeResponse = {
  groups: [
    {
      id: 'grp-4',
      system_name: 'digital-presence',
      name: 'Presencia Digital',
      sort_order: 30,
      sections: [
        {
          id: 's1-6',
          level: 1,
          system_name: 'linkedin-publish',
          label: 'LinkedIn · Publicar',
          path: '/linkedin',
          section_type: 'functional',
          sort_order: 10,
          origin: 'code',
          has_layout: true,
          view_count: 1,
          views: [mainView],
          children: [],
        },
        {
          id: 's1-7',
          level: 1,
          system_name: 'career-publications',
          label: 'Publicaciones',
          path: '/career/publications',
          section_type: 'table',
          sort_order: 20,
          origin: 'code',
          has_layout: true,
          view_count: 1,
          views: [{ ...mainView, id: 'vw-13', key: 'list', label: 'Lista' }],
          children: [],
        },
      ],
    },
    {
      id: 'grp-11',
      system_name: 'support',
      name: 'Soporte',
      sort_order: 160,
      sections: [
        {
          id: 's1-53',
          level: 1,
          system_name: 'career-tags',
          label: 'Tags',
          path: '/career/tags',
          section_type: 'table',
          sort_order: 160,
          origin: 'code',
          has_layout: true,
          view_count: 1,
          views: [{ ...mainView, id: 'vw-14', key: 'list', label: 'Lista' }],
          children: [],
        },
      ],
    },
  ],
  generated_at: '2026-08-28T12:00:00Z',
}

const sampleDetail: SectionDetail = {
  id: 's1-6',
  level: 1,
  system_name: 'linkedin-publish',
  label: 'LinkedIn · Publicar',
  path: '/linkedin',
  section_type: 'functional',
  sort_order: 10,
  origin: 'code',
  group_id: 'grp-4',
  parent_id: null,
  view_count: 1,
  views: sampleTree.groups[0].sections[0].views,
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
    mockedNavTree.get.mockResolvedValue(sampleTree)
    mockedSections.get.mockResolvedValue(sampleDetail)
    mockedSections.reorder.mockResolvedValue([])
    mockedGroups.reorder.mockResolvedValue([])
  })

  it('lists the nav tree grouped by group, with type and view count', async () => {
    renderAt('/settings/sections')
    await waitFor(() => expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument())
    expect(screen.getByText('Presencia Digital')).toBeInTheDocument()
    expect(screen.getByText('funcional')).toBeInTheDocument()
    expect(screen.getByText('s1-6')).toBeInTheDocument()
    expect(screen.getByText('linkedin-publish')).toBeInTheDocument()
  })

  it('opens a section detail from the tree and shows its views', async () => {
    renderAt('/settings/sections')
    await waitFor(() => expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument())
    fireEvent.click(screen.getByText('LinkedIn · Publicar'))
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Secciones del Admin')
    )
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('s1-6')
    expect(screen.getByText('linkedin-publish')).toBeInTheDocument()
    expect(screen.getByText('Principal')).toBeInTheDocument()
  })

  it('links to Settings → Vistas to edit the responsible agent and instructions', async () => {
    renderAt('/settings/sections/s1-6')
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('s1-6')
    )
    expect(
      screen.getByRole('button', { name: /ver vistas de esta sección/i })
    ).toBeInTheDocument()
  })

  it('moves a section down within its own group via the move buttons', async () => {
    renderAt('/settings/sections')
    await waitFor(() => expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: 'Bajar LinkedIn · Publicar' }))

    await waitFor(() =>
      expect(mockedSections.reorder).toHaveBeenCalledWith({
        container_id: 'grp-4',
        order: ['s1-7', 's1-6'],
      })
    )
  })

  it('disables "subir" on the first section and "bajar" on the last section of a group', async () => {
    renderAt('/settings/sections')
    await waitFor(() => expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument())

    expect(screen.getByRole('button', { name: 'Subir LinkedIn · Publicar' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Bajar Publicaciones' })).toBeDisabled()
  })

  it('moves a group down via the group-level move buttons', async () => {
    renderAt('/settings/sections')
    await waitFor(() => expect(screen.getByText('Presencia Digital')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: 'Bajar grupo Presencia Digital' }))

    await waitFor(() =>
      expect(mockedGroups.reorder).toHaveBeenCalledWith(['grp-11', 'grp-4'])
    )
  })

  it('does not navigate to the section detail when a move button inside the row is clicked', async () => {
    renderAt('/settings/sections')
    await waitFor(() => expect(screen.getByText('LinkedIn · Publicar')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: 'Bajar LinkedIn · Publicar' }))

    expect(screen.queryByText('Ver vistas de esta sección en Settings → Vistas →')).not.toBeInTheDocument()
  })
})
