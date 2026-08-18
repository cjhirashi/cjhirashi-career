import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '../utils'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useThemeStore } from '@/stores/themeStore'

describe('ThemeToggle', () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: 'system', resolvedTheme: 'light' })
    document.documentElement.removeAttribute('data-theme')
  })

  it('should render a group with the three theme options', () => {
    render(<ThemeToggle />)
    expect(screen.getByRole('group', { name: 'Tema' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tema claro' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tema del sistema' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tema oscuro' })).toBeInTheDocument()
  })

  it('should mark the active theme option as pressed', () => {
    useThemeStore.setState({ theme: 'dark', resolvedTheme: 'dark' })
    render(<ThemeToggle />)
    expect(screen.getByRole('button', { name: 'Tema oscuro' })).toHaveAttribute(
      'aria-pressed',
      'true'
    )
    expect(screen.getByRole('button', { name: 'Tema claro' })).toHaveAttribute(
      'aria-pressed',
      'false'
    )
  })

  it('should update the store when clicking a theme option', () => {
    render(<ThemeToggle />)
    fireEvent.click(screen.getByRole('button', { name: 'Tema claro' }))
    expect(useThemeStore.getState().theme).toBe('light')

    fireEvent.click(screen.getByRole('button', { name: 'Tema oscuro' }))
    expect(useThemeStore.getState().theme).toBe('dark')
  })

  it('should move the sliding indicator to match the active option', () => {
    const { container, rerender } = render(<ThemeToggle />)
    let indicator = container.querySelector('.theme-pill-indicator')
    expect(indicator).toHaveAttribute('data-pos', '1') // system = index 1

    useThemeStore.setState({ theme: 'dark', resolvedTheme: 'dark' })
    rerender(<ThemeToggle />)
    indicator = container.querySelector('.theme-pill-indicator')
    expect(indicator).toHaveAttribute('data-pos', '2') // dark = index 2
  })

  it('should apply data-theme to <html> when a theme is selected', () => {
    render(<ThemeToggle />)
    fireEvent.click(screen.getByRole('button', { name: 'Tema oscuro' }))
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })
})
