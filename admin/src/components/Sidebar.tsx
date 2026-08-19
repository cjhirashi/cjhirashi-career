import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import { ChevronDown, Menu, LayoutDashboard, BarChart3, FolderOpen, Linkedin } from 'lucide-react'
import { CAREER_DOMAINS, CAREER_RESOURCES } from '@/config/careerResources'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

// Only the pages that still have real, standalone content. Every other
// legacy menu item (Identity/Competencies/Evidence/Job Strategies/
// Networking/Interviews) pointed at pre-career-domain (v1) pages superseded
// by the 30 resources under CAREER_DOMAINS below — removed rather than kept
// as dead links (see also App.tsx, which no longer routes to them).
const menuItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Métricas', path: '/metrics', icon: BarChart3 },
  { label: 'Archivos', path: '/files', icon: FolderOpen },
]

// LinkedIn isn't a generic career resource (no /career/:resourceKey page -
// it's the standalone OAuth/posting page at /linkedin), so it can't just be
// added to a domain's `resourceKeys` like the other 30 - it's spliced into
// the "Presencia Digital" accordion's rendering below instead, by key.
const LINKEDIN_DOMAIN_KEY = 'digital'

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const location = useLocation()
  // Which career domain accordion is expanded ("Identidad Profesional",
  // "Operativa de Búsqueda", ...). At most one at a time to keep the list
  // manageable - there are 30 resources across 5 domains. Domains render
  // directly in the sidebar (no outer "Carrera" wrapper to expand first).
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null)

  const isActive = (path: string): boolean => location.pathname === path
  const isCareerResourceActive = (resourceKey: string): boolean =>
    location.pathname === `/career/${resourceKey}`

  const closeMobileDrawer = () => {
    if (window.innerWidth < 768 && isOpen) onToggle()
  }

  const handleDomainToggle = (domainKey: string) => {
    // When the sidebar itself is collapsed (icon-only, desktop), clicking a
    // domain expands the sidebar first instead of trying to render a
    // sub-menu with no room for labels.
    if (!isOpen) {
      onToggle()
      setExpandedDomain(domainKey)
      return
    }
    setExpandedDomain((current) => (current === domainKey ? null : domainKey))
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
      <div className="p-4 border-b border-border flex items-center justify-end">
        <button
          onClick={onToggle}
          className="p-2 hover:bg-glass rounded-xl transition-colors"
          title={isOpen ? 'Contraer' : 'Expandir'}
        >
          <Menu size={20} aria-hidden="true" />
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
            <item.icon size={20} className="flex-shrink-0" aria-hidden="true" />
            {isOpen && <span className="text-sm font-medium truncate">{item.label}</span>}
          </Link>
        ))}

        {/* Career domain (v2) - the 30 resources, grouped into 5 logical
            domains (Identidad Profesional, Operativa de Búsqueda, Presencia
            Digital, Networking, Soporte - see careerResources.ts). Each
            domain is its own collapsible section directly in the sidebar,
            in the order the domains are approved/declared - no outer
            "Carrera" wrapper to expand first. */}
        <div className="pt-2 mt-2 border-t border-border space-y-1">
          {CAREER_DOMAINS.map((domain) => {
            const isDomainExpanded = expandedDomain === domain.key
            return (
              <div key={domain.key}>
                <button
                  type="button"
                  onClick={() => handleDomainToggle(domain.key)}
                  className="sidebar-item w-full justify-between"
                  title={isOpen ? undefined : domain.label}
                  aria-expanded={isDomainExpanded}
                >
                  <span className="flex items-center gap-3 min-w-0">
                    <domain.icon size={20} className="flex-shrink-0" aria-hidden="true" />
                    {isOpen && <span className="text-sm font-medium truncate">{domain.label}</span>}
                  </span>
                  {isOpen && (
                    <ChevronDown
                      size={16}
                      className={clsx('flex-shrink-0 transition-transform', isDomainExpanded && 'rotate-180')}
                    />
                  )}
                </button>

                {isOpen && isDomainExpanded && (
                  <div className="mt-1 space-y-0.5 mb-1">
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
                    {domain.key === LINKEDIN_DOMAIN_KEY && (
                      <Link
                        to="/linkedin"
                        onClick={closeMobileDrawer}
                        aria-current={isActive('/linkedin') ? 'page' : undefined}
                        className={clsx(
                          'flex items-center gap-1.5 pl-12 pr-4 py-1.5 rounded-xl text-sm truncate transition-colors',
                          isActive('/linkedin')
                            ? 'text-primary bg-primary-light'
                            : 'text-text-secondary hover:bg-glass hover:text-text'
                        )}
                      >
                        <Linkedin size={13} className="flex-shrink-0" aria-hidden="true" />
                        LinkedIn · Publicar
                      </Link>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </nav>

      {/* Footer - just the version. User identity (avatar/name/role) already
          lives in the Navbar dropdown at the top - no need to repeat it
          here too. */}
      {isOpen && (
        <div className="p-3 border-t border-border">
          <p className="text-[11px] text-text-muted text-center">v0.1.0</p>
        </div>
      )}
    </aside>
  )
}
