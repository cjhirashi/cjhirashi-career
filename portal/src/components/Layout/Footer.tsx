import { Link } from 'react-router-dom'
import { useTrackClick } from '@/hooks/useTracking'
import { useContact } from '@/hooks/useContact'

export const Footer = () => {
  const { trackClick } = useTrackClick()
  const { data: contact } = useContact()

  const handleSocialClick = (label: string) => {
    trackClick(`social-${label.toLowerCase()}`)
  }

  const socialLinks = [
    ...(contact?.github_url ? [{ label: 'GitHub', href: contact.github_url }] : []),
    ...(contact?.linkedin_url ? [{ label: 'LinkedIn', href: contact.linkedin_url }] : []),
    ...(contact?.footer_links ?? []).map(link => ({ label: link.label, href: link.url })),
  ]

  return (
    <footer className="section-alt text-text-secondary mt-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div>
            <h3 className="text-lg font-bold text-text mb-2">Carlos Jiménez Hirashi</h3>
            <p className="text-text-secondary text-sm">AI Solutions Architect</p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-semibold text-text mb-4">Navegación</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/" className="text-text-secondary hover:text-primary transition">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-text-secondary hover:text-primary transition">
                  Sobre Mí
                </Link>
              </li>
              <li>
                <Link to="/projects" className="text-text-secondary hover:text-primary transition">
                  Proyectos
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold text-text mb-4">Recursos</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/blog" className="text-text-secondary hover:text-primary transition">
                  Blog
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-text-secondary hover:text-primary transition">
                  Contacto
                </Link>
              </li>
              {contact?.contact_email && (
                <li>
                  <a
                    href={`mailto:${contact.contact_email}`}
                    className="text-text-secondary hover:text-primary transition"
                  >
                    {contact.contact_email}
                  </a>
                </li>
              )}
            </ul>
          </div>

          {/* Social */}
          {socialLinks.length > 0 && (
            <div>
              <h4 className="font-semibold text-text mb-4">Sígueme</h4>
              <ul className="space-y-2 text-sm">
                {socialLinks.map(link => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => handleSocialClick(link.label)}
                      className="text-text-secondary hover:text-primary transition"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-border pt-8">
          <p className="text-sm text-text-secondary">
            © {new Date().getFullYear()} Carlos Jiménez Hirashi. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </footer>
  )
}
