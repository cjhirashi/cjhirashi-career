import React, { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { PanelRight } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'
import { SidebarRight } from './SidebarRight'

interface LayoutProps {
  children: React.ReactNode
}

const MOBILE_BREAKPOINT = 768 // Tailwind's `md` breakpoint

const isDesktopViewport = (): boolean =>
  typeof window !== 'undefined' ? window.innerWidth >= MOBILE_BREAKPOINT : true

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  // Sidebar is expanded by default on desktop, and closed (off-canvas) by
  // default on mobile - it doubles as "expanded/collapsed" on desktop and
  // "open/closed drawer" on mobile.
  const [sidebarOpen, setSidebarOpen] = useState(isDesktopViewport)
  // Right panel (chat/instructions) - open by default on desktop; the panel
  // itself only ever renders from the `xl` breakpoint up regardless (see
  // SidebarRight.tsx), this just tracks the user's show/hide choice.
  const [rightPanelOpen, setRightPanelOpen] = useState(true)
  const { logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    let wasDesktop = isDesktopViewport()

    const handleResize = (): void => {
      const isDesktop = isDesktopViewport()
      // Only react when crossing the breakpoint, so we don't fight a user's
      // manual expand/collapse choice on every pixel of resizing.
      if (isDesktop !== wasDesktop) {
        setSidebarOpen(isDesktop)
        wasDesktop = isDesktop
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const closeMobileSidebar = (): void => {
    if (!isDesktopViewport()) setSidebarOpen(false)
  }

  return (
    // `dash-wrapper`: the body (see index.css) carries the Glass Steel
    // ambient gradient - this stays transparent so it's visible through the
    // glass chrome (topbar/sidebars) and behind the (also translucent)
    // `.card` panels rendered by each page.
    <div className="flex flex-col h-screen text-text overflow-hidden">
      {/* Topbar (`dash-topbar`) - full-width, sticky, glass. */}
      <Navbar
        onLogout={handleLogout}
        onMenuToggle={() => setSidebarOpen((open) => !open)}
        onRightPanelToggle={() => setRightPanelOpen((open) => !open)}
        rightPanelOpen={rightPanelOpen}
      />

      {/* `dash-body`: sidebar-left | main-content | sidebar-right */}
      <div className="flex flex-1 min-h-0">
        <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen((open) => !open)} />

        {/* Mobile backdrop - dims content and closes the drawer on click */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 bg-slate-900/50 md:hidden"
            aria-hidden="true"
            onClick={closeMobileSidebar}
          />
        )}

        {/* Main Content (`main-content`) */}
        <main className="flex-1 overflow-auto min-w-0">
          <div className="p-4 sm:p-6 max-w-7xl mx-auto">{children}</div>
        </main>

        {/* Chat (reserved for the future in-Admin Bedrock assistant) /
            instructions panel - see SidebarRight.tsx. `xl:` and up only,
            and only when the user hasn't hidden it via the topbar toggle. */}
        {rightPanelOpen ? (
          <SidebarRight onClose={() => setRightPanelOpen(false)} />
        ) : (
          // Edge tab to bring the panel back - same idea as the collapsed
          // left Sidebar always leaving a strip to re-expand from, so
          // hiding the right panel is never a dead end.
          <button
            type="button"
            onClick={() => setRightPanelOpen(true)}
            aria-label="Mostrar panel de asistencia"
            title="Mostrar panel"
            className="hidden xl:flex items-center justify-center w-8 flex-shrink-0 glass-panel backdrop-blur-[20px] border-l border-border text-text-secondary hover:text-text hover:bg-glass transition-colors"
          >
            <PanelRight size={18} aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  )
}
