import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, PanelRight } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { ThemeToggle } from './ThemeToggle'
import { clsx } from 'clsx'

interface NavbarProps {
  onLogout: () => void
  /** Only rendered on mobile (<md). Opens/closes the off-canvas sidebar. */
  onMenuToggle?: () => void
  /** Shows/hides the right panel (chat/instructions) - `xl:` and up only,
   * mirrors where SidebarRight itself renders. */
  onRightPanelToggle?: () => void
  rightPanelOpen?: boolean
}

export const Navbar: React.FC<NavbarProps> = ({
  onLogout,
  onMenuToggle,
  onRightPanelToggle,
  rightPanelOpen,
}) => {
  const { user } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)

  return (
    <header className="sticky top-0 z-20 glass-panel backdrop-blur-[16px] border-b border-border">
      <div className="px-4 sm:px-6 py-4 flex items-center justify-between gap-3">
        {/* Mobile menu toggle - only present when Layout wires it up */}
        {onMenuToggle && (
          <button
            type="button"
            onClick={onMenuToggle}
            aria-label="Abrir menú de navegación"
            className="md:hidden p-2 -ml-2 rounded-lg text-text-secondary hover:bg-glass focus:outline-none focus:ring-2 focus:ring-cyan-500 flex-shrink-0"
          >
            <Menu size={22} aria-hidden="true" />
          </button>
        )}

        {/* Left side - Breadcrumb or title placeholder */}
        <div className="flex-1 min-w-0">
          <h1 className="text-lg sm:text-xl font-semibold text-text truncate">
            Welcome to Admin Panel
          </h1>
        </div>

        {/* Right side - Theme toggle + user menu + panel toggle */}
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          <ThemeToggle />

          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              aria-label="User menu"
              aria-haspopup="true"
              aria-expanded={dropdownOpen}
              className={clsx(
                'flex items-center space-x-2 px-2 sm:px-4 py-2 rounded-xl transition-colors',
                'hover:bg-glass focus:outline-none focus:ring-2 focus:ring-cyan-500'
              )}
            >
              <div className="w-8 h-8 bg-cyan-600 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-glow">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="text-sm text-text hidden sm:block text-left">
                <p className="font-medium">{user?.full_name || user?.username}</p>
                <p className="text-xs text-text-secondary">{user?.email}</p>
              </div>
              <span className="text-text-muted hidden sm:inline">▼</span>
            </button>

            {/* Dropdown menu */}
            {dropdownOpen && (
              <div
                className="absolute right-0 mt-2 w-56 max-w-[90vw] z-50 rounded-2xl border shadow-glass"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-glass)', backdropFilter: 'blur(16px)' }}
              >
                {/* Not `.card` on purpose - avoids the hover lift/glow-border
                    treatment that `.card` applies for content panels, which
                    would feel wrong on this ephemeral popover menu. */}
                <div className="p-4 border-b border-border">
                  <p className="text-sm font-medium text-text">{user?.full_name}</p>
                  <p className="text-xs text-text-secondary">{user?.email}</p>
                </div>
                <nav className="p-2 space-y-1">
                  <Link
                    to="/change-password"
                    onClick={() => setDropdownOpen(false)}
                    className="block px-4 py-2 text-sm text-text hover:bg-glass rounded-lg transition-colors"
                  >
                    Change Password
                  </Link>
                </nav>
                <div className="border-t border-border p-2">
                  <button
                    onClick={() => {
                      setDropdownOpen(false)
                      onLogout()
                    }}
                    className="w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg transition-colors text-left"
                  >
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Panel toggle sits at the far edge, adjacent to where
              SidebarRight itself opens - keeps the spatial link between
              the control and what it controls, instead of living among
              unrelated view/account controls. */}
          {onRightPanelToggle && (
            <button
              type="button"
              onClick={onRightPanelToggle}
              aria-label={rightPanelOpen ? 'Ocultar panel de asistencia' : 'Mostrar panel de asistencia'}
              aria-pressed={rightPanelOpen}
              title={rightPanelOpen ? 'Ocultar panel' : 'Mostrar panel'}
              className="hidden xl:flex p-2 rounded-xl text-text-secondary hover:bg-glass hover:text-text focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-colors"
            >
              <PanelRight size={20} aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
