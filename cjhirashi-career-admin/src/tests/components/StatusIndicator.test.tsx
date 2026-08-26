import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { StatusIndicator } from '@/components/StatusIndicator'

describe('StatusIndicator', () => {
  it('shows Activo without a switch when the value is on', () => {
    render(<StatusIndicator active />)
    expect(screen.getByRole('status')).toHaveTextContent('Activo')
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()
  })

  it('shows Inactivo when the value is off', () => {
    render(<StatusIndicator active={false} />)
    expect(screen.getByRole('status')).toHaveTextContent('Inactivo')
  })
})
