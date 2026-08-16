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
    <footer className="bg-slate-900 text-white mt-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div>
            <h3 className="text-lg font-bold mb-2">Carlos Jiménez Hirashi</h3>
            <p className="text-slate-400 text-sm">Solutions Architect & Portfolio Professional</p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-semibold mb-4">Navigation</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/" className="text-slate-400 hover:text-cyan-400 transition">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-slate-400 hover:text-cyan-400 transition">
                  About
                </Link>
              </li>
              <li>
                <Link to="/projects" className="text-slate-400 hover:text-cyan-400 transition">
                  Projects
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/blog" className="text-slate-400 hover:text-cyan-400 transition">
                  Blog
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-slate-400 hover:text-cyan-400 transition">
                  Contact
                </Link>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-cyan-400 transition">
                  Sitemap
                </a>
              </li>
            </ul>
          </div>

          {/* Social */}
          <div>
            <h4 className="font-semibold mb-4">Follow</h4>
            <div className="flex space-x-4">
              {socialLinks.map(link => (
                <a
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => handleSocialClick(link.label)}
                  className="text-slate-400 hover:text-cyan-400 transition text-lg"
                  aria-label={link.label}
                >
                  {link.icon}
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-700 pt-8">
          <div className="flex justify-between items-center text-sm text-slate-400">
            <p>© 2024 Carlos Jiménez Hirashi. All rights reserved.</p>
            <div className="flex space-x-4">
              <a href="#" className="hover:text-cyan-400 transition">
                Privacy
              </a>
              <a href="#" className="hover:text-cyan-400 transition">
                Terms
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
