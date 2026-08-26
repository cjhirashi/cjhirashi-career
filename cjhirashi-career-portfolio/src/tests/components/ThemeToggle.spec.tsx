import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeToggle } from '@/components/Common/ThemeToggle'
import { useUIStore } from '@/stores/uiStore'
import { THEME_STORAGE_KEY } from '@/utils/theme'

describe('ThemeToggle', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useUIStore.setState({ theme: 'system', resolvedTheme: 'light' })
  })

  afterEach(() => {
    useUIStore.setState({ theme: 'system', resolvedTheme: 'light' })
  })

  it('renders a group with light/system/dark buttons', () => {
    render(<ThemeToggle />)

    expect(screen.getByRole('group', { name: 'Tema' })).toBeInTheDocument()
    expect(screen.getByLabelText('Tema claro')).toBeInTheDocument()
    expect(screen.getByLabelText('Tema del sistema')).toBeInTheDocument()
    expect(screen.getByLabelText('Tema oscuro')).toBeInTheDocument()
  })

  it('marks the active mode as aria-pressed', () => {
    useUIStore.setState({ theme: 'system' })
    render(<ThemeToggle />)

    expect(screen.getByLabelText('Tema del sistema')).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByLabelText('Tema claro')).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByLabelText('Tema oscuro')).toHaveAttribute('aria-pressed', 'false')
  })

  it('clicking "dark" switches the theme and persists it', async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)

    await user.click(screen.getByLabelText('Tema oscuro'))

    expect(useUIStore.getState().theme).toBe('dark')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(screen.getByLabelText('Tema oscuro')).toHaveAttribute('aria-pressed', 'true')
  })

  it('clicking "light" switches the theme back and updates the DOM', async () => {
    const user = userEvent.setup()
    useUIStore.getState().setTheme('dark')
    render(<ThemeToggle />)

    await user.click(screen.getByLabelText('Tema claro'))

    expect(useUIStore.getState().theme).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('moves the sliding indicator to match the active mode', () => {
    useUIStore.setState({ theme: 'dark' })
    const { container } = render(<ThemeToggle />)

    const indicator = container.querySelector('.theme-pill-indicator')
    expect(indicator).toHaveAttribute('data-pos', '2')
  })
})
