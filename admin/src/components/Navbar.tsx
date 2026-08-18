import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { ThemeToggle } from './ThemeToggle'
import { clsx } from 'clsx'

interface NavbarProps {
  onLogout: () => void
  /** Only rendered on mobile (<md). Opens/closes the off-canvas sidebar. */
  onMenuToggle?: () => void
}

export const Navbar: React.FC<NavbarProps> = ({ onLogout, onMenuToggle }) => {
  const { user } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)

  return (
    <header className="bg-white dark:bg-surface-card border-b border-slate-200 dark:border-border shadow-sm">
      <div className="px-4 sm:px-6 py-4 flex items-center justify-between gap-3">
        {/* Mobile menu toggle - only present when Layout wires it up */}
        {onMenuToggle && (
          <button
            type="button"
            onClick={onMenuToggle}
            aria-label="Abrir menú de navegación"
            className="md:hidden p-2 -ml-2 rounded-lg text-slate-600 dark:text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 flex-shrink-0"
          >
            <Menu size={22} aria-hidden="true" />
          </button>
        )}

        {/* Left side - Breadcrumb or title placeholder */}
        <div className="flex-1 min-w-0">
          <h1 className="text-lg sm:text-xl font-semibold text-slate-900 dark:text-slate-100 truncate">
            Welcome to Admin Panel
          </h1>
        </div>

        {/* Right side - Theme toggle + user menu */}
        <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
          <ThemeToggle />

          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              aria-label="User menu"
              aria-haspopup="true"
              aria-expanded={dropdownOpen}
              className={clsx(
                'flex items-center space-x-2 px-2 sm:px-4 py-2 rounded-lg transition-colors',
                'hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-cyan-500'
              )}
            >
              <div className="w-8 h-8 bg-cyan-600 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="text-sm text-slate-900 dark:text-slate-100 hidden sm:block text-left">
                <p className="font-medium">{user?.full_name || user?.username}</p>
                <p className="text-xs text-slate-500 dark:text-text-secondary">{user?.email}</p>
              </div>
              <span className="text-slate-400 dark:text-text-secondary hidden sm:inline">▼</span>
            </button>

            {/* Dropdown menu */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 max-w-[90vw] bg-white dark:bg-surface-card rounded-lg shadow-lg border border-slate-200 dark:border-border z-50">
                <div className="p-4 border-b border-slate-200 dark:border-border">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{user?.full_name}</p>
                  <p className="text-xs text-slate-500 dark:text-text-secondary">{user?.email}</p>
                </div>
                <nav className="p-2 space-y-1">
                  <Link
                    to="/change-password"
                    onClick={() => setDropdownOpen(false)}
                    className="block px-4 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors"
                  >
                    Change Password
                  </Link>
                </nav>
                <div className="border-t border-slate-200 dark:border-border p-2">
                  <button
                    onClick={() => {
                      setDropdownOpen(false)
                      onLogout()
                    }}
                    className="w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded transition-colors text-left"
                  >
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
