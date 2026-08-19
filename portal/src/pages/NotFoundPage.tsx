import { Link } from 'react-router-dom'
import { useTrackClick } from '@/hooks/useTracking'

export const NotFoundPage = () => {
  const { trackClick } = useTrackClick()

  const handleBackHome = () => {
    trackClick('404-home')
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-cyan-50/40 to-slate-50/40 dark:from-slate-900/40 dark:to-slate-950/40">
      <div className="card text-center p-10 sm:p-16">
        {/* 404 */}
        <div className="mb-8">
          <h1 className="text-7xl sm:text-8xl md:text-9xl font-bold text-primary [text-shadow:0_0_30px_var(--primary-glow)]">
            404
          </h1>
          <p className="text-2xl font-bold text-text">Page Not Found</p>
        </div>

        {/* Message */}
        <p className="text-lg text-text-secondary max-w-md mx-auto mb-8">
          Oops! It looks like the page you're looking for doesn't exist. Let me help you get back
          on track.
        </p>

        {/* CTA */}
        <div className="space-y-4">
          <Link to="/" onClick={handleBackHome} className="btn inline-flex px-8 py-3 font-semibold">
            Back to Home
          </Link>

          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/about"
              className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-medium"
            >
              About
            </Link>
            <span className="text-border">•</span>
            <Link
              to="/projects"
              className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-medium"
            >
              Projects
            </Link>
            <span className="text-border">•</span>
            <Link
              to="/contact"
              className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-medium"
            >
              Contact
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
