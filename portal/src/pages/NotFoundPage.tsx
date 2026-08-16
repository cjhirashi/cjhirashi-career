import { Link } from 'react-router-dom'
import { useTrackClick } from '@/hooks/useTracking'

export const NotFoundPage = () => {
  const { trackClick } = useTrackClick()

  const handleBackHome = () => {
    trackClick('404-home')
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-cyan-50 to-slate-50">
      <div className="text-center">
        {/* 404 */}
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-cyan-600">404</h1>
          <p className="text-2xl font-bold text-slate-900">Page Not Found</p>
        </div>

        {/* Message */}
        <p className="text-lg text-slate-600 max-w-md mx-auto mb-8">
          Oops! It looks like the page you're looking for doesn't exist. Let me help you get back
          on track.
        </p>

        {/* CTA */}
        <div className="space-y-4">
          <Link
            to="/"
            onClick={handleBackHome}
            className="inline-block bg-cyan-600 hover:bg-cyan-700 text-white px-8 py-3 rounded-lg font-semibold transition"
          >
            Back to Home
          </Link>

          <div className="flex justify-center gap-4">
            <Link to="/about" className="text-cyan-600 hover:text-cyan-700 font-medium">
              About
            </Link>
            <span className="text-slate-300">•</span>
            <Link to="/projects" className="text-cyan-600 hover:text-cyan-700 font-medium">
              Projects
            </Link>
            <span className="text-slate-300">•</span>
            <Link to="/contact" className="text-cyan-600 hover:text-cyan-700 font-medium">
              Contact
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
