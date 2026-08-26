import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { StateCapsule } from '@/components/StateCapsule'

describe('StateCapsule', () => {
  it('shows only the human label, not a machine-key rail', () => {
    render(<StateCapsule tone="pending" label="Pendiente" />)
    expect(screen.getByText('Pendiente')).toBeInTheDocument()
    expect(screen.queryByText('pending')).not.toBeInTheDocument()
    expect(screen.getByText('Pendiente').closest('[data-tone]')).toHaveAttribute('data-tone', 'pending')
  })

  it('maps priority tones independently', () => {
    render(<StateCapsule tone="high" label="Alta" />)
    expect(screen.getByText('Alta').closest('[data-tone]')).toHaveAttribute('data-tone', 'high')
  })
})
