import { useTrackClick } from '@/hooks/useTracking'
import { useContact } from '@/hooks/useContact'

/** Matches cjhirashi.com's real footer: just the copyright line and 4
 * social icons - deliberately no Navegación/Recursos columns. */
export const Footer = () => {
  const { trackClick } = useTrackClick()
  const { data: contact } = useContact()

  const handleSocialClick = (label: string) => {
    trackClick(`social-${label.toLowerCase()}`)
  }

  const socialLinks = [
    ...(contact?.github_url ? [{ label: 'GitHub', href: contact.github_url }] : []),
    ...(contact?.linkedin_url ? [{ label: 'LinkedIn', href: contact.linkedin_url }] : []),
    ...(contact?.contact_email ? [{ label: 'Email', href: `mailto:${contact.contact_email}` }] : []),
    ...(contact?.whatsapp
      ? [{ label: 'WhatsApp', href: `https://wa.me/${contact.whatsapp.replace(/\D/g, '')}` }]
      : []),
  ]

  return (
    <footer className="text-text-secondary mt-16 border-t border-border">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-sm">© {new Date().getFullYear()} Carlos A. Jiménez Hirashi</p>

        {socialLinks.length > 0 && (
          <div className="flex items-center gap-5">
            {socialLinks.map(link => (
              <a
                key={link.label}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => handleSocialClick(link.label)}
                aria-label={link.label}
                title={link.label}
                className="text-text-secondary hover:text-primary transition text-sm font-medium"
              >
                {link.label}
              </a>
            ))}
          </div>
        )}
      </div>
    </footer>
  )
}
