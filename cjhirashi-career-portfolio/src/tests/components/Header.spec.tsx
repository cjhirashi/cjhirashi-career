import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '../testUtils'
import { Header } from '@/components/Layout/Header'

vi.mock('@/api/contact')

describe('Header Component', () => {
  it('renders navigation links', () => {
    render(<Header />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Sobre Mí')).toBeInTheDocument()
    expect(screen.getByText('Proyectos')).toBeInTheDocument()
  })

  it('renders logo', () => {
    render(<Header />)

    expect(screen.getByAltText('cjhirashi')).toBeInTheDocument()
  })

  it('has navigation links with correct href attributes', () => {
    render(<Header />)

    const homeLink = screen.getByRole('link', { name: /home/i })
    expect(homeLink).toHaveAttribute('href', '/')
  })
})
