import { Link } from 'react-router-dom'
import { useTrackClick } from '@/hooks/useTracking'

export const NotFoundPage = () => {
  const { trackClick } = useTrackClick()

  const handleBackHome = () => {
    trackClick('404-home')
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-cyan-50 to-slate-50 dark:from-slate-900 dark:to-slate-950">
      <div className="text-center">
        {/* 404 */}
        <div className="mb-8">
          <h1 className="text-7xl sm:text-8xl md:text-9xl font-bold text-primary">404</h1>
          <p className="text-2xl font-bold text-text">Page Not Found</p>
        </div>

        {/* Message */}
        <p className="text-lg text-text-secondary max-w-md mx-auto mb-8">
          Oops! It looks like the page you're looking for doesn't exist. Let me help you get back
          on track.
        </p>

        {/* CTA */}
        <div className="space-y-4">
          <Link
            to="/"
            onClick={handleBackHome}
            className="inline-block bg-primary hover:opacity-90 text-on-primary px-8 py-3 rounded-lg font-semibold transition"
          >
            Back to Home
          </Link>

          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/about" className="text-primary hover:opacity-80 font-medium">
              About
            </Link>
            <span className="text-border">•</span>
            <Link to="/projects" className="text-primary hover:opacity-80 font-medium">
              Projects
            </Link>
            <span className="text-border">•</span>
            <Link to="/contact" className="text-primary hover:opacity-80 font-medium">
              Contact
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
