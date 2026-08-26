import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '../utils'
import { ThemedSwitch } from '@/components/ThemedSwitch'

describe('ThemedSwitch', () => {
  it('toggles from off to on with a sliding switch, not a checkbox', () => {
    const onChange = vi.fn()
    render(<ThemedSwitch aria-label="Activo" checked={false} onChange={onChange} />)

    const control = screen.getByRole('switch', { name: 'Activo' })
    expect(control).toHaveAttribute('aria-checked', 'false')
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()

    fireEvent.click(control)
    expect(onChange).toHaveBeenCalledWith(true)
  })

  it('does not toggle when disabled', () => {
    const onChange = vi.fn()
    render(<ThemedSwitch aria-label="Activo" checked={true} onChange={onChange} disabled />)

    fireEvent.click(screen.getByRole('switch', { name: 'Activo' }))
    expect(onChange).not.toHaveBeenCalled()
  })
})
