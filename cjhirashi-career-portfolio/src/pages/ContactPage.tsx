import { useState } from 'react'
import { useContact } from '@/hooks/useContact'
import { useTrackClick } from '@/hooks/useTracking'
import { trackingApi } from '@/api/tracking'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'

export const ContactPage = () => {
  const { data: contact, isLoading, error } = useContact()
  const [formData, setFormData] = useState({ name: '', email: '', message: '' })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const { trackClick } = useTrackClick()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // No backend endpoint receives this yet (no SMTP/delivery pipeline) -
      // only the click gets tracked. Wire a real /public/contact-message
      // endpoint here when that's actually needed.
      trackingApi.trackEvent({
        type: 'form_submit',
        page: '/contact',
        target: 'contact-form',
        metadata: { name: formData.name, email: formData.email },
      })

      setSubmitted(true)
      setFormData({ name: '', email: '', message: '' })
      setTimeout(() => setSubmitted(false), 5000)
    } catch (err) {
      console.error('Failed to send message:', err)
    } finally {
      setLoading(false)
    }
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudo cargar la información de contacto" />

  const whatsappHref = contact?.whatsapp ? `https://wa.me/${contact.whatsapp.replace(/\D/g, '')}` : null

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-text mb-4">Hablemos de tu proyecto</h1>
          <p className="text-lg text-text-secondary">
            Sistemas de datos, IA o automatización crítica que no pueden fallar. Cuéntame qué estás construyendo.
          </p>
        </div>

        <div className="grid grid-cols-1 content:grid-cols-3 gap-8 mb-12">
          {/* Contact Info */}
          <div className="content:col-span-1 space-y-6">
            {contact?.contact_email && (
              <div className="card p-4">
                <h3 className="font-bold text-text mb-2">Email</h3>
                <a
                  href={`mailto:${contact.contact_email}`}
                  className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] break-all"
                >
                  {contact.contact_email}
                </a>
              </div>
            )}

            {contact?.whatsapp && whatsappHref && (
              <div className="card p-4">
                <h3 className="font-bold text-text mb-2">WhatsApp</h3>
                <a
                  href={whatsappHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => trackClick('contact-whatsapp')}
                  className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)]"
                >
                  {contact.whatsapp}
                </a>
              </div>
            )}

            {contact?.location && (
              <div className="card p-4">
                <h3 className="font-bold text-text mb-2">Ubicación</h3>
                <p className="text-text-secondary">{contact.location}</p>
              </div>
            )}

            {(contact?.linkedin_url || contact?.github_url) && (
              <div className="card p-4">
                <h3 className="font-bold text-text mb-2">Sígueme</h3>
                <div className="space-y-2">
                  {contact?.linkedin_url && (
                    <a
                      href={contact.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => trackClick('social-linkedin')}
                      className="block text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)]"
                    >
                      LinkedIn
                    </a>
                  )}
                  {contact?.github_url && (
                    <a
                      href={contact.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => trackClick('social-github')}
                      className="block text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)]"
                    >
                      GitHub
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Contact Form */}
          <div className="content:col-span-2">
            {submitted ? (
              <div className="bg-green-50 dark:bg-green-950/40 backdrop-blur-lg border border-green-200 dark:border-green-900 rounded-md p-8 text-center">
                <div className="text-4xl mb-4">✓</div>
                <h3 className="text-xl font-bold text-green-900 dark:text-green-200 mb-2">¡Mensaje enviado!</h3>
                <p className="text-green-700 dark:text-green-300">Gracias por escribir. Te responderé pronto.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="card p-6 space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-text mb-2">
                    Nombre
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="input-field"
                    placeholder="Tu nombre"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-text mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="input-field"
                    placeholder="tu@email.com"
                  />
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-text mb-2">
                    Mensaje
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="input-field"
                    placeholder="Tu mensaje..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  onClick={() => trackClick('contact-submit')}
                  className="btn w-full font-semibold py-3"
                >
                  {loading ? 'Enviando...' : 'Enviar mensaje'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
