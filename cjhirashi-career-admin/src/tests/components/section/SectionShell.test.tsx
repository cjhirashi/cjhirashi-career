import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent } from '../../utils'
import { SectionShell } from '@/components/section/SectionShell'

const tabs = [
  { key: 'list', label: 'Lista' },
  { key: 'view', label: 'Detalle' },
]

describe('SectionShell', () => {
  it('renders a list title with count badge and its tabs', () => {
    render(
      <MemoryRouter>
        <SectionShell title="Reportes" count={4} tabs={tabs} activeTab="list" variant="list">
          <div>cuerpo</div>
        </SectionShell>
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: /Reportes/ })).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('cuerpo')).toBeInTheDocument()
  })

  it('renders the record breadcrumb and fires onTabSelect for interactive tabs', () => {
    const onTabSelect = vi.fn()
    render(
      <MemoryRouter>
        <SectionShell
          breadcrumb={{ section: 'Reportes', id: 'err-3', name: 'api:POST /x' }}
          tabs={tabs}
          activeTab="view"
          interactiveTabs={['list']}
          onTabSelect={onTabSelect}
        >
          <div>detalle</div>
        </SectionShell>
      </MemoryRouter>,
    )
    expect(screen.getByText('err-3')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: 'Lista' }))
    expect(onTabSelect).toHaveBeenCalledWith('list')
  })
})
