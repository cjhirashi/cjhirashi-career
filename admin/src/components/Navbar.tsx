import React, { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { clsx } from 'clsx'

interface NavbarProps {
  onLogout: () => void
}

export const Navbar: React.FC<NavbarProps> = ({ onLogout }) => {
  const { user } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)

  return (
    <header className="bg-white border-b border-slate-200 shadow-sm">
      <div className="px-6 py-4 flex items-center justify-between">
        {/* Left side - Breadcrumb or title placeholder */}
        <div className="flex-1">
          <h1 className="text-xl font-semibold text-slate-900">
            Welcome to Admin Panel
          </h1>
        </div>

        {/* Right side - User menu */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className={clsx(
              'flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors',
              'hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500'
            )}
          >
            <div className="w-8 h-8 bg-cyan-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="text-sm text-slate-900">
              <p className="font-medium">{user?.full_name || user?.username}</p>
              <p className="text-xs text-slate-500">{user?.email}</p>
            </div>
            <span className="text-slate-400">▼</span>
          </button>

          {/* Dropdown menu */}
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 z-50">
              <div className="p-4 border-b border-slate-200">
                <p className="text-sm font-medium text-slate-900">{user?.full_name}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
              <nav className="p-2 space-y-1">
                <a
                  href="/profile"
                  className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded transition-colors"
                >
                  Profile Settings
                </a>
                <a
                  href="/change-password"
                  className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded transition-colors"
                >
                  Change Password
                </a>
              </nav>
              <div className="border-t border-slate-200 p-2">
                <button
                  onClick={() => {
                    setDropdownOpen(false)
                    onLogout()
                  }}
                  className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded transition-colors text-left"
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
