import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

const menuItems = [
  { label: 'Dashboard', path: '/dashboard', icon: '📊' },
  { label: 'Identity', path: '/identity', icon: '👤' },
  { label: 'Competencies', path: '/competencies', icon: '🎯' },
  { label: 'Evidence', path: '/evidence', icon: '📁' },
  { label: 'Job Strategies', path: '/job-strategies', icon: '🔍' },
  { label: 'Networking', path: '/networking', icon: '🤝' },
  { label: 'Interviews', path: '/interviews', icon: '💼' },
  { label: 'Metrics', path: '/metrics', icon: '📈' },
]

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const location = useLocation()

  const isActive = (path: string): boolean => location.pathname === path

  return (
    <aside
      className={clsx(
        'bg-slate-800 text-white transition-all duration-300 flex flex-col border-r border-slate-700',
        isOpen ? 'w-64' : 'w-20'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-700 flex items-center justify-between">
        {isOpen && <h1 className="text-lg font-bold text-cyan-400">Portfolio</h1>}
        <button
          onClick={onToggle}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          title={isOpen ? 'Collapse' : 'Expand'}
        >
          ☰
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={clsx(
              'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
              isActive(item.path)
                ? 'bg-cyan-600 text-white'
                : 'text-slate-300 hover:bg-slate-700'
            )}
            title={isOpen ? undefined : item.label}
          >
            <span className="text-xl flex-shrink-0">{item.icon}</span>
            {isOpen && <span className="text-sm font-medium">{item.label}</span>}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700 text-xs text-slate-400 text-center">
        {isOpen && <p>v0.1.0</p>}
      </div>
    </aside>
  )
}
