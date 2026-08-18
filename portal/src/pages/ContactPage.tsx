import { useState } from 'react'
import { useTrackClick } from '@/hooks/useTracking'
import { trackingApi } from '@/api/tracking'

export const ContactPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const { trackClick } = useTrackClick()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Track form submission
      trackingApi.trackEvent({
        type: 'form_submit',
        page: '/contact',
        target: 'contact-form',
        metadata: {
          name: formData.name,
          email: formData.email,
        },
      })

      // Send message (if backend supports it)
      // const response = await contactApi.sendMessage(formData)

      // For now, just show success
      setSubmitted(true)
      setFormData({ name: '', email: '', subject: '', message: '' })

      // Reset after 5 seconds
      setTimeout(() => setSubmitted(false), 5000)
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-text mb-4">Get in Touch</h1>
          <p className="text-lg text-text-secondary">
            Have a question or want to work together? I'd love to hear from you.
          </p>
        </div>

        <div className="grid grid-cols-1 content:grid-cols-3 gap-8 mb-12">
          {/* Contact Info */}
          <div className="content:col-span-1 space-y-6">
            {/* Email */}
            <div>
              <h3 className="font-bold text-text mb-2">Email</h3>
              <a
                href="mailto:cjhirashi@gmail.com"
                className="text-primary hover:opacity-80 break-all"
              >
                cjhirashi@gmail.com
              </a>
            </div>

            {/* Social */}
            <div>
              <h3 className="font-bold text-text mb-2">Follow</h3>
              <div className="space-y-2">
                <a href="#" className="block text-primary hover:opacity-80">
                  GitHub
                </a>
                <a href="#" className="block text-primary hover:opacity-80">
                  LinkedIn
                </a>
                <a href="#" className="block text-primary hover:opacity-80">
                  Twitter
                </a>
              </div>
            </div>

            {/* Response Time */}
            <div className="bg-primary-container p-4 rounded-lg">
              <p className="text-xs uppercase font-bold text-primary mb-1">Response Time</p>
              <p className="text-text">Usually within 24 hours</p>
            </div>
          </div>

          {/* Contact Form */}
          <div className="content:col-span-2">
            {submitted ? (
              <div className="bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-900 rounded-lg p-8 text-center">
                <div className="text-4xl mb-4">✓</div>
                <h3 className="text-xl font-bold text-green-900 dark:text-green-200 mb-2">
                  Message Sent!
                </h3>
                <p className="text-green-700 dark:text-green-300">
                  Thank you for reaching out. I'll get back to you soon.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Name */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-text mb-2">
                    Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-2 bg-surface-card border border-border text-text rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-600 dark:focus:ring-primary"
                    placeholder="Your name"
                  />
                </div>

                {/* Email */}
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
                    className="w-full px-4 py-2 bg-surface-card border border-border text-text rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-600 dark:focus:ring-primary"
                    placeholder="your@email.com"
                  />
                </div>

                {/* Subject */}
                <div>
                  <label htmlFor="subject" className="block text-sm font-medium text-text mb-2">
                    Subject
                  </label>
                  <input
                    type="text"
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    className="w-full px-4 py-2 bg-surface-card border border-border text-text rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-600 dark:focus:ring-primary"
                    placeholder="What's this about?"
                  />
                </div>

                {/* Message */}
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-text mb-2">
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="w-full px-4 py-2 bg-surface-card border border-border text-text rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-600 dark:focus:ring-primary"
                    placeholder="Your message..."
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={loading}
                  onClick={() => trackClick('contact-submit')}
                  className="w-full bg-primary hover:opacity-90 disabled:opacity-50 text-on-primary font-semibold py-3 rounded-lg transition"
                >
                  {loading ? 'Sending...' : 'Send Message'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
