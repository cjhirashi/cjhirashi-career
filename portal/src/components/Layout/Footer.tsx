import { Link } from 'react-router-dom'
import { useTrackClick } from '@/hooks/useTracking'

interface SocialLink {
  label: string
  href: string
  icon: string
}

const socialLinks: SocialLink[] = [
  {
    label: 'GitHub',
    href: 'https://github.com',
    icon: '📱',
  },
  {
    label: 'LinkedIn',
    href: 'https://linkedin.com',
    icon: '💼',
  },
  {
    label: 'Twitter',
    href: 'https://twitter.com',
    icon: '🐦',
  },
]

export const Footer = () => {
  const { trackClick } = useTrackClick()

  const handleSocialClick = (label: string) => {
    trackClick(`social-${label.toLowerCase()}`)
  }

  return (
    <footer className="section-alt text-text-secondary mt-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div>
            <h3 className="text-lg font-bold text-text mb-2">Carlos Jiménez Hirashi</h3>
            <p className="text-text-secondary text-sm">
              Solutions Architect & Portfolio Professional
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-semibold text-text mb-4">Navigation</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/" className="text-text-secondary hover:text-primary transition">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-text-secondary hover:text-primary transition">
                  About
                </Link>
              </li>
              <li>
                <Link
                  to="/projects"
                  className="text-text-secondary hover:text-primary transition"
                >
                  Projects
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold text-text mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/blog" className="text-text-secondary hover:text-primary transition">
                  Blog
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-text-secondary hover:text-primary transition">
                  Contact
                </Link>
              </li>
              <li>
                <a href="#" className="text-text-secondary hover:text-primary transition">
                  Sitemap
                </a>
              </li>
            </ul>
          </div>

          {/* Social */}
          <div>
            <h4 className="font-semibold text-text mb-4">Follow</h4>
            <div className="flex space-x-4">
              {socialLinks.map(link => (
                <a
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => handleSocialClick(link.label)}
                  className="text-text-secondary hover:text-primary transition text-lg"
                  aria-label={link.label}
                >
                  {link.icon}
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-border pt-8">
          <div className="flex justify-between items-center text-sm text-text-secondary">
            <p>© 2024 Carlos Jiménez Hirashi. All rights reserved.</p>
            <div className="flex space-x-4">
              <a href="#" className="hover:text-primary transition">
                Privacy
              </a>
              <a href="#" className="hover:text-primary transition">
                Terms
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
