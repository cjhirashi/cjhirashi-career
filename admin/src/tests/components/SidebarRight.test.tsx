import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '../utils'
import { MemoryRouter } from 'react-router-dom'
import { SidebarRight } from '@/components/SidebarRight'

const renderAt = (pathname: string, onClose = vi.fn()) =>
  render(
    <MemoryRouter initialEntries={[pathname]}>
      <SidebarRight onClose={onClose} />
    </MemoryRouter>
  )

describe('SidebarRight', () => {
  it('should default to the "Instrucciones" tab, not the chat placeholder', () => {
    renderAt('/dashboard')
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.queryByText('Asistente IA')).not.toBeInTheDocument()
  })

  it('should switch to the chat placeholder when the chat tab is pressed', () => {
    renderAt('/dashboard')
    fireEvent.click(screen.getByTitle('Chat del asistente'))
    expect(screen.getByText('Asistente IA')).toBeInTheDocument()
    expect(screen.getByText('Próximamente')).toBeInTheDocument()
  })

  it('should switch back to instructions when that tab is pressed again', () => {
    renderAt('/dashboard')
    fireEvent.click(screen.getByTitle('Chat del asistente'))
    fireEvent.click(screen.getByTitle('Instrucciones de la pantalla'))
    expect(screen.queryByText('Asistente IA')).not.toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('should call onClose when the hide button is clicked', () => {
    const onClose = vi.fn()
    renderAt('/dashboard', onClose)
    fireEvent.click(screen.getByLabelText('Ocultar panel'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('should show metrics-specific instructions on /metrics', () => {
    renderAt('/metrics')
    expect(screen.getByText('Métricas')).toBeInTheDocument()
  })

  it('should derive instructions for a career-domain resource from its own config', () => {
    renderAt('/career/vacancies')
    expect(screen.getByText('Vacantes')).toBeInTheDocument()
    expect(screen.getByText(/Nueva Vacante/)).toBeInTheDocument()
  })

  it('should show a singleton-specific instruction for a singleton resource (e.g. identity)', () => {
    renderAt('/career/identity')
    expect(screen.getByText(/único registro/)).toBeInTheDocument()
  })

  it('should fall back to a generic message for an unknown route', () => {
    renderAt('/some-unmapped-route')
    expect(screen.getByText('Esta pantalla')).toBeInTheDocument()
  })

  it('should only be visible from the xl breakpoint up', () => {
    const { container } = renderAt('/dashboard')
    const aside = container.querySelector('aside')
    expect(aside?.className).toContain('hidden')
    expect(aside?.className).toContain('xl:flex')
  })
})
