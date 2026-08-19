import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Header } from '@/components/Layout/Header'

describe('Header Component', () => {
  it('renders navigation links', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Sobre Mí')).toBeInTheDocument()
    expect(screen.getByText('Proyectos')).toBeInTheDocument()
  })

  it('renders logo', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    expect(screen.getByAltText('cjhirashi')).toBeInTheDocument()
  })

  it('has navigation links with correct href attributes', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    )

    const homeLink = screen.getByRole('link', { name: /home/i })
    expect(homeLink).toHaveAttribute('href', '/')
  })
})
