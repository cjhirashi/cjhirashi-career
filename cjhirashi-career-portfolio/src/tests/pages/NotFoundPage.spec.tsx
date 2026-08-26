import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { NotFoundPage } from '@/pages/NotFoundPage'

describe('NotFoundPage', () => {
  it('renders 404 heading', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    )

    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('renders "not found" message', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Página no encontrada')).toBeInTheDocument()
  })

  it('renders the "back to home" link', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    )

    const homeLink = screen.getByRole('link', { name: /volver a home/i })
    expect(homeLink).toHaveAttribute('href', '/')
  })

  it('renders navigation links', () => {
    render(
      <BrowserRouter>
        <NotFoundPage />
      </BrowserRouter>
    )

    expect(screen.getByRole('link', { name: /sobre mí/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /proyectos/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /contacto/i })).toBeInTheDocument()
  })
})
