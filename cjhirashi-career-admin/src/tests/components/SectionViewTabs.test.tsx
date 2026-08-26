import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent } from '../utils'
import { SectionViewTabs } from '@/components/SectionViewTabs'

describe('SectionViewTabs', () => {
  const views = [
    { key: 'list', label: 'Lista' },
    { key: 'view', label: 'Vista' },
    { key: 'edit', label: 'Edición' },
  ]

  it('marks the active view tab and reports the others as inactive', () => {
    render(
      <MemoryRouter>
        <SectionViewTabs views={views} activeKey="list" interactiveKeys={['list']} onSelect={() => undefined} />
      </MemoryRouter>
    )
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Vista' })).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByRole('tab', { name: 'Edición' })).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByRole('tab', { name: 'Lista' }).tagName).toBe('BUTTON')
    expect(screen.getByRole('tab', { name: 'Vista' }).tagName).not.toBe('BUTTON')
  })

  it('notifies only when an interactive tab is chosen', () => {
    const onSelect = vi.fn()
    render(
      <MemoryRouter>
        <SectionViewTabs views={views} activeKey="view" interactiveKeys={['list']} onSelect={onSelect} />
      </MemoryRouter>
    )
    fireEvent.click(screen.getByRole('tab', { name: 'Vista' }))
    expect(onSelect).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('tab', { name: 'Lista' }))
    expect(onSelect).toHaveBeenCalledWith('list')
  })

  it('renders an icon inside each tab for the mobile label replacement', () => {
    render(
      <MemoryRouter>
        <SectionViewTabs views={views} activeKey="list" interactiveKeys={['list']} onSelect={() => undefined} />
      </MemoryRouter>
    )
    expect(screen.getByRole('tab', { name: 'Lista' }).querySelector('svg')).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Vista' }).querySelector('svg')).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Edición' }).querySelector('svg')).toBeTruthy()
  })
})
