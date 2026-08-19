import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import { ChevronDown } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { CAREER_DOMAINS, CAREER_RESOURCES } from '@/config/careerResources'

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
  const { user } = useAuth()
  // Which career domain accordion is expanded ("Identidad Profesional",
  // "Operativa de Búsqueda", ...). At most one at a time to keep the list
  // manageable - there are 30 resources across 5 domains.
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null)
  // Whether the "Carrera" section itself (the 5 domains) is expanded.
  const [careerSectionOpen, setCareerSectionOpen] = useState(false)

  const isActive = (path: string): boolean => location.pathname === path
  const isCareerResourceActive = (resourceKey: string): boolean =>
    location.pathname === `/career/${resourceKey}`

  const closeMobileDrawer = () => {
    if (window.innerWidth < 768 && isOpen) onToggle()
  }

  const handleCareerSectionToggle = () => {
    // When the sidebar itself is collapsed (icon-only, desktop), clicking the
    // "Carrera" icon expands the sidebar first instead of trying to render a
    // sub-menu with no room for labels.
    if (!isOpen) {
      onToggle()
      setCareerSectionOpen(true)
      return
    }
    setCareerSectionOpen((open) => !open)
  }

  return (
    <aside
      className={clsx(
        // Glass Steel chrome: translucent, blurred glass panel (see
        // `.glass-panel` / `--bg-glass` in src/index.css) instead of the
        // previous flat, always-dark slate-800 background - it now adapts
        // to the active theme like the rest of the app.
        'glass-panel backdrop-blur-[20px] text-text transition-all duration-300 flex flex-col border-r border-border',
        // Mobile: off-canvas drawer that slides in/out over the content.
        // Desktop (md+): back in normal flow, width toggles expanded/collapsed.
        'fixed inset-y-0 left-0 z-40 md:static md:z-auto md:translate-x-0',
        isOpen ? 'translate-x-0 w-64' : '-translate-x-full w-64 md:translate-x-0 md:w-20'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        {isOpen && <h1 className="text-lg font-bold text-primary">Portfolio</h1>}
        <button
          onClick={onToggle}
          className="p-2 hover:bg-glass rounded-xl transition-colors"
          title={isOpen ? 'Collapse' : 'Expand'}
        >
          ☰
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            onClick={() => {
              // Close the drawer after navigating on mobile.
              if (window.innerWidth < 768 && isOpen) onToggle()
            }}
            aria-current={isActive(item.path) ? 'page' : undefined}
            className={clsx('sidebar-item', isActive(item.path) && 'is-active')}
            title={isOpen ? undefined : item.label}
          >
            <span className="text-xl flex-shrink-0">{item.icon}</span>
            {isOpen && <span className="text-sm font-medium truncate">{item.label}</span>}
          </Link>
        ))}

        {/* Career domain (v2) - collapsible section grouping the 30
            career-domain resources into 5 sub-menus, see
            src/config/careerResources.ts (CAREER_DOMAINS). */}
        <div className="pt-2 mt-2 border-t border-border">
          <button
            type="button"
            onClick={handleCareerSectionToggle}
            className="sidebar-item w-full justify-between"
            title={isOpen ? undefined : 'Carrera'}
            aria-expanded={careerSectionOpen}
          >
            <span className="flex items-center gap-3 min-w-0">
              <span className="text-xl flex-shrink-0">🚀</span>
              {isOpen && <span className="text-sm font-medium truncate">Carrera</span>}
            </span>
            {isOpen && (
              <ChevronDown
                size={16}
                className={clsx('flex-shrink-0 transition-transform', careerSectionOpen && 'rotate-180')}
              />
            )}
          </button>

          {isOpen && careerSectionOpen && (
            <div className="mt-1 space-y-1">
              {CAREER_DOMAINS.map((domain) => {
                const isDomainExpanded = expandedDomain === domain.key
                return (
                  <div key={domain.key}>
                    <button
                      type="button"
                      onClick={() => setExpandedDomain((current) => (current === domain.key ? null : domain.key))}
                      className="sidebar-section-label w-full flex items-center justify-between hover:bg-glass hover:text-text rounded-xl transition-colors"
                      aria-expanded={isDomainExpanded}
                    >
                      <span className="flex items-center gap-2 truncate">
                        <span aria-hidden="true">{domain.icon}</span>
                        <span className="truncate">{domain.label}</span>
                      </span>
                      <ChevronDown
                        size={12}
                        className={clsx('flex-shrink-0 transition-transform', isDomainExpanded && 'rotate-180')}
                      />
                    </button>

                    {isDomainExpanded && (
                      <div className="space-y-0.5 mb-1">
                        {domain.resourceKeys.map((resourceKey) => {
                          const resource = CAREER_RESOURCES[resourceKey]
                          if (!resource) return null
                          const path = `/career/${resourceKey}`
                          const active = isCareerResourceActive(resourceKey)
                          return (
                            <Link
                              key={resourceKey}
                              to={path}
                              onClick={closeMobileDrawer}
                              aria-current={active ? 'page' : undefined}
                              className={clsx(
                                'block pl-12 pr-4 py-1.5 rounded-xl text-sm truncate transition-colors',
                                active ? 'text-primary bg-primary-light' : 'text-text-secondary hover:bg-glass hover:text-text'
                              )}
                            >
                              {resource.label}
                            </Link>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </nav>

      {/* Footer - profile summary (avatar, name, role). The theme toggle
          lives in the topbar (Navbar) so it's always reachable even when
          this sidebar is off-canvas on mobile - see Navbar.tsx. */}
      <div className="p-3 border-t border-border">
        {isOpen ? (
          <div className="sidebar-profile">
            <div className="w-9 h-9 rounded-full bg-cyan-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-glow">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-text truncate">{user?.full_name || user?.username}</p>
              <p className="text-xs text-text-muted truncate">{user?.professional_title || 'Administrador'}</p>
            </div>
          </div>
        ) : (
          <div className="w-9 h-9 mx-auto rounded-full bg-cyan-600 flex items-center justify-center text-white font-bold text-sm shadow-glow">
            {user?.username?.charAt(0).toUpperCase() || 'U'}
          </div>
        )}
        {isOpen && <p className="text-[11px] text-text-muted text-center mt-2">v0.1.0</p>}
      </div>
    </aside>
  )
}
