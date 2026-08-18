import React, { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'

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
    <div className="flex h-screen bg-bg text-text overflow-hidden">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen((open) => !open)} />

      {/* Mobile backdrop - dims content and closes the drawer on click */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/50 md:hidden"
          aria-hidden="true"
          onClick={closeMobileSidebar}
        />
      )}

      {/* Main Content */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Navbar */}
        <Navbar onLogout={handleLogout} onMenuToggle={() => setSidebarOpen((open) => !open)} />

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <div className="p-4 sm:p-6 max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  )
}
