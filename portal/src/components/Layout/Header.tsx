import { Link, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import { useTrackClick } from '@/hooks/useTracking'
import { useUIStore } from '@/stores/uiStore'
import { ThemeToggle } from '@/components/Common/ThemeToggle'

interface NavLink {
  label: string
  href: string
}

const navLinks: NavLink[] = [
  { label: 'Home', href: '/' },
  { label: 'About', href: '/about' },
  { label: 'Projects', href: '/projects' },
  { label: 'Blog', href: '/blog' },
  { label: 'Contact', href: '/contact' },
]

export const Header = () => {
  const mobileMenuOpen = useUIStore(state => state.mobileMenuOpen)
  const toggleMobileMenu = useUIStore(state => state.toggleMobileMenu)
  const setMobileMenuOpen = useUIStore(state => state.setMobileMenuOpen)
  // The wordmark's text color is baked into the SVG itself (dark text for
  // light backgrounds, light text for dark ones), so swap the whole file
  // instead of trying to theme it via CSS.
  const resolvedTheme = useUIStore(state => state.resolvedTheme)
  const logoSrc = resolvedTheme === 'dark' ? '/logo-dark.svg' : '/logo-light.svg'
  const location = useLocation()
  const { trackClick } = useTrackClick()

  const handleNavClick = (label: string) => {
    trackClick(`nav-${label.toLowerCase()}`)
    setMobileMenuOpen(false)
  }

  const isActive = (href: string) => location.pathname === href

  return (
    <header className="sticky top-0 z-50 bg-bg-glass backdrop-blur-lg border-b border-border">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 gap-2">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center flex-shrink-0"
            onClick={() => handleNavClick('logo')}
          >
            <img src={logoSrc} alt="cjhirashi" className="h-7 w-auto" />
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map(link => (
              <Link
                key={link.href}
                to={link.href}
                onClick={() => handleNavClick(link.label)}
                className={clsx(
                  'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive(link.href)
                    ? 'text-cyan-600 bg-cyan-50 dark:text-cyan-300 dark:bg-cyan-950/40 [text-shadow:0_0_10px_var(--primary-glow)]'
                    : 'text-slate-600 hover:text-cyan-600 hover:[text-shadow:0_0_10px_var(--primary-glow)] dark:text-slate-300 dark:hover:text-cyan-300'
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Theme Toggle - always visible, desktop and mobile */}
          <div className="flex items-center gap-1">
            <ThemeToggle />

            {/* Mobile Menu Button */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-md text-slate-600 hover:text-cyan-600 hover:bg-bg-card dark:text-slate-300 dark:hover:text-cyan-300"
              aria-label="Toggle menu"
              aria-expanded={mobileMenuOpen}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-4 border-t border-border">
            {navLinks.map(link => (
              <Link
                key={link.href}
                to={link.href}
                onClick={() => handleNavClick(link.label)}
                className={clsx(
                  'block px-3 py-2 mt-1 rounded-md text-base font-medium transition-colors',
                  isActive(link.href)
                    ? 'text-cyan-600 bg-cyan-50 dark:text-cyan-300 dark:bg-cyan-950/40'
                    : 'text-slate-600 hover:text-cyan-600 hover:bg-bg-card dark:text-slate-300 dark:hover:text-cyan-300'
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </nav>
    </header>
  )
}
