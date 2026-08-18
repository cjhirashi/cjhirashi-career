import { Monitor, Moon, Sun } from 'lucide-react'
import { useUIStore } from '@/stores/uiStore'
import { ThemeMode } from '@/types'
import { THEME_MODES } from '@/utils/theme'

interface ThemeOption {
  mode: ThemeMode
  label: string
  icon: typeof Sun
}

const THEME_OPTIONS: ThemeOption[] = [
  { mode: 'light', label: 'Tema claro', icon: Sun },
  { mode: 'system', label: 'Tema del sistema', icon: Monitor },
  { mode: 'dark', label: 'Tema oscuro', icon: Moon },
]

/**
 * 3-way theme switch (light / system / dark) with a sliding indicator,
 * matching the mechanism used on cjhirashi.com. Always visible in the
 * header, works on both desktop and mobile.
 */
export const ThemeToggle = () => {
  const theme = useUIStore(state => state.theme)
  const setTheme = useUIStore(state => state.setTheme)

  const activeIndex = Math.max(THEME_MODES.indexOf(theme), 0)

  return (
    <div className="theme-pill" role="group" aria-label="Tema">
      <span className="theme-pill-indicator" data-pos={activeIndex} aria-hidden="true" />
      {THEME_OPTIONS.map(({ mode, label, icon: Icon }) => (
        <button
          key={mode}
          type="button"
          data-theme-val={mode}
          aria-label={label}
          aria-pressed={theme === mode}
          className="theme-pill-btn"
          onClick={() => setTheme(mode)}
        >
          <Icon size={16} strokeWidth={2} aria-hidden="true" />
        </button>
      ))}
    </div>
  )
}
