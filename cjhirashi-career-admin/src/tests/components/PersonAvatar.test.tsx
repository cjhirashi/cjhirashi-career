import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { PersonChip, initialsFromName } from '@/components/PersonAvatar'

describe('initialsFromName', () => {
  it('uses first and last word', () => {
    expect(initialsFromName('Carlos Jiménez')).toBe('CJ')
  })
})

describe('PersonChip', () => {
  it('renders a capsule with photo and name, without an id rail', () => {
    render(
      <PersonChip
        variant="capsule"
        src="https://example.com/agent.png"
        name="Control de búsqueda de vacantes"
      />
    )
    const chip = screen.getByText('Control de búsqueda de vacantes').closest('.actor-capsule')
    expect(chip).toBeTruthy()
    expect(chip?.querySelector('img')?.getAttribute('src')).toBe('https://example.com/agent.png')
    expect(screen.queryByText('agent')).not.toBeInTheDocument()
    expect(screen.queryByText('user')).not.toBeInTheDocument()
  })

  it('falls back to initials when there is no photo', () => {
    render(<PersonChip variant="capsule" name="Demo User" />)
    expect(screen.getByText('Demo User').closest('.actor-capsule')).toHaveTextContent('DU')
  })
})
