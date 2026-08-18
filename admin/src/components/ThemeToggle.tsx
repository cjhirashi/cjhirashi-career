import React from 'react'
import { Sun, Monitor, Moon } from 'lucide-react'
import { useThemeStore, ThemeMode } from '@/stores/themeStore'

interface ThemeOption {
  value: ThemeMode
  label: string
  Icon: typeof Sun
}

const THEME_OPTIONS: ThemeOption[] = [
  { value: 'light', label: 'Tema claro', Icon: Sun },
  { value: 'system', label: 'Tema del sistema', Icon: Monitor },
  { value: 'dark', label: 'Tema oscuro', Icon: Moon },
]

/**
 * Three-way theme selector (light / system / dark) with a sliding pill
 * indicator, matching the mechanism used on cjhirashi.com.
 */
export const ThemeToggle: React.FC = () => {
  const theme = useThemeStore((state) => state.theme)
  const setTheme = useThemeStore((state) => state.setTheme)

  const activeIndex = Math.max(
    0,
    THEME_OPTIONS.findIndex((option) => option.value === theme)
  )

  return (
    <div className="theme-pill" role="group" aria-label="Tema">
      {THEME_OPTIONS.map(({ value, label, Icon }) => (
        <button
          key={value}
          type="button"
          data-theme-val={value}
          aria-label={label}
          aria-pressed={theme === value}
          onClick={() => setTheme(value)}
          className="theme-pill-btn"
        >
          <Icon size={16} strokeWidth={2} aria-hidden="true" />
        </button>
      ))}
      <span className="theme-pill-indicator" data-pos={activeIndex} aria-hidden="true" />
    </div>
  )
}
