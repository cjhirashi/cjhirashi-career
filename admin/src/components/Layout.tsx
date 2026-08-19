import React, { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
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
      <Navbar onLogout={handleLogout} onMenuToggle={() => setSidebarOpen((open) => !open)} />

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

        {/* Reserved for the future in-Admin Bedrock assistant - see
            SidebarRight.tsx. `xl:` and up only. */}
        <SidebarRight />
      </div>
    </div>
  )
}
