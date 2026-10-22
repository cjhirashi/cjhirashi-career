import type { SVGProps } from 'react'
import { Github, Linkedin, Mail } from 'lucide-react'
import { useTrackClick } from '@/hooks/useTracking'
import { useContact } from '@/hooks/useContact'

/** lucide-react has no WhatsApp glyph (brand icons are out of scope for that
 * set), so it's inlined here to match the other icons' size/stroke API. */
const WhatsAppIcon = ({ size = 20, ...props }: SVGProps<SVGSVGElement> & { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
    {...props}
  >
    <path d="M17.472 14.382c-.297-.149-1.758-.868-2.03-.967-.273-.099-.47-.148-.669.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
    <path d="M12.041 2C6.496 2 2 6.476 2 11.994c0 1.993.588 3.85 1.6 5.411L2 22l4.71-1.555a10.09 10.09 0 0 0 5.331 1.521h.004c5.545 0 10.04-4.476 10.042-9.994 0-2.67-1.04-5.179-2.93-7.064A10.013 10.013 0 0 0 12.041 2Zm0 18.168h-.003a8.157 8.157 0 0 1-4.168-1.14l-.299-.177-3.096 1.023.84-3.5-.199-.33a8.13 8.13 0 0 1-1.262-4.37c0-4.502 3.68-8.166 8.164-8.166a8.14 8.14 0 0 1 5.783 2.4 8.1 8.1 0 0 1 2.39 5.785c-.002 4.502-3.68 8.475-8.15 8.475Z" />
  </svg>
)

/** Matches cjhirashi.com's real footer: just the copyright line and 4
 * social icons - deliberately no Navegación/Recursos columns. */
export const Footer = () => {
  const { trackClick } = useTrackClick()
  const { data: contact } = useContact()

  const handleSocialClick = (label: string) => {
    trackClick(`social-${label.toLowerCase()}`)
  }

  const socialLinks = [
    ...(contact?.github_url ? [{ label: 'GitHub', href: contact.github_url, Icon: Github }] : []),
    ...(contact?.linkedin_url
      ? [{ label: 'LinkedIn', href: contact.linkedin_url, Icon: Linkedin }]
      : []),
    ...(contact?.contact_email
      ? [{ label: 'Email', href: `mailto:${contact.contact_email}`, Icon: Mail }]
      : []),
    ...(contact?.whatsapp
      ? [
          {
            label: 'WhatsApp',
            href: `https://wa.me/${contact.whatsapp.replace(/\D/g, '')}`,
            Icon: WhatsAppIcon,
          },
        ]
      : []),
  ]

  return (
    <footer className="text-text-secondary mt-16 border-t border-border">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-sm">© {new Date().getFullYear()} Carlos A. Jiménez Hirashi</p>

        {socialLinks.length > 0 && (
          <div className="flex items-center gap-5">
            {socialLinks.map(({ label, href, Icon }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => handleSocialClick(label)}
                aria-label={label}
                title={label}
                className="text-text-secondary hover:text-primary transition"
              >
                <Icon size={20} strokeWidth={2} aria-hidden="true" />
              </a>
            ))}
          </div>
        )}
      </div>
    </footer>
  )
}
