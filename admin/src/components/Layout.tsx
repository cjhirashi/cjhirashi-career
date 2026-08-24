import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { PanelRight } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'
import { SidebarRight } from './SidebarRight'

interface LayoutProps {
  children: React.ReactNode
}

const MOBILE_BREAKPOINT = 768 // Tailwind's `md` breakpoint
const DESKTOP_BREAKPOINT = 1280 // Tailwind's `xl` breakpoint - matches SidebarRight's own

/** Chat contextual (sidebar derecha) no se muestra en Chat General — ya tiene su propia UI. */
const CONTEXTUAL_CHAT_HIDDEN_ROUTES = ['/agent/chat']

const isContextualChatHidden = (pathname: string): boolean =>
  CONTEXTUAL_CHAT_HIDDEN_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`))

const isDesktopViewport = (): boolean =>
  typeof window !== 'undefined' ? window.innerWidth >= MOBILE_BREAKPOINT : true

const isXlViewport = (): boolean =>
  typeof window !== 'undefined' ? window.innerWidth >= DESKTOP_BREAKPOINT : true

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  // Sidebar is expanded by default on desktop, and closed (off-canvas) by
  // default on mobile - it doubles as "expanded/collapsed" on desktop and
  // "open/closed drawer" on mobile.
  const [sidebarOpen, setSidebarOpen] = useState(isDesktopViewport)
  // Right panel (chat/instructions) - open by default on desktop (xl+),
  // where it lives in normal flow; closed by default below that, where it's
  // a full-screen (mobile) or right-anchored (tablet) overlay instead - see
  // SidebarRight.tsx - so it doesn't cover the work area on first load.
  const [rightPanelOpen, setRightPanelOpen] = useState(isXlViewport)
  const { logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const hideContextualChat = isContextualChatHidden(pathname)

  useEffect(() => {
    if (hideContextualChat) setRightPanelOpen(false)
  }, [hideContextualChat])

  useEffect(() => {
    let wasDesktop = isDesktopViewport()
    let wasXl = isXlViewport()

    const handleResize = (): void => {
      // Only react when crossing a breakpoint, so we don't fight a user's
      // manual expand/collapse choice on every pixel of resizing.
      const isDesktop = isDesktopViewport()
      if (isDesktop !== wasDesktop) {
        setSidebarOpen(isDesktop)
        wasDesktop = isDesktop
      }

      const isXl = isXlViewport()
      if (isXl !== wasXl && !hideContextualChat) {
        setRightPanelOpen(isXl)
        wasXl = isXl
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [hideContextualChat])

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
        onRightPanelToggle={hideContextualChat ? undefined : () => setRightPanelOpen((open) => !open)}
        rightPanelOpen={hideContextualChat ? false : rightPanelOpen}
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

        {/* Backdrop for the right panel's overlay modes (mobile full-screen,
            tablet right-anchored) - dims the work area and closes it on
            click, same idea as the left sidebar's mobile backdrop above.
            Not needed at `xl:` and up, where the panel lives in normal flow
            instead of floating over the content. */}
        {rightPanelOpen && !hideContextualChat && (
          <div
            className="fixed inset-0 z-40 bg-slate-900/50 xl:hidden"
            aria-hidden="true"
            onClick={() => setRightPanelOpen(false)}
          />
        )}

        {!hideContextualChat &&
          (rightPanelOpen ? (
            <SidebarRight onClose={() => setRightPanelOpen(false)} />
          ) : (
            <button
              type="button"
              onClick={() => setRightPanelOpen(true)}
              aria-label="Mostrar panel de asistencia"
              title="Mostrar panel"
              className="hidden md:flex items-center justify-center w-8 flex-shrink-0 glass-panel backdrop-blur-[20px] border-l border-border text-text-secondary hover:text-text hover:bg-glass transition-colors"
            >
              <PanelRight size={18} aria-hidden="true" />
            </button>
          ))}
      </div>
    </div>
  )
}
