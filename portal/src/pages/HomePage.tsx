import { Link } from 'react-router-dom'
import { useIdentity, useCompetencies } from '@/hooks/useIdentity'
import { useFeaturedProjects } from '@/hooks/useProjects'
import { useTrackClick } from '@/hooks/useTracking'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'

export const HomePage = () => {
  const { data: identity, isLoading: identityLoading, error: identityError } = useIdentity()
  const { data: competencies } = useCompetencies()
  const {
    data: featuredProjects,
    isLoading: projectsLoading,
    error: projectsError,
  } = useFeaturedProjects(3)
  const { trackClick } = useTrackClick()

  const handleCTA = (action: string) => {
    trackClick(`hero-${action}`)
  }

  if (identityLoading) return <LoadingSpinner />
  if (identityError) return <ErrorMessage message="Failed to load profile" />

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-cyan-50 to-slate-50">
        <div className="mx-auto max-w-4xl">
          <div className="text-center">
            {/* Avatar */}
            {identity?.avatar && (
              <div className="mb-6 flex justify-center">
                <img
                  src={identity.avatar}
                  alt={identity.name}
                  className="w-24 h-24 rounded-full border-4 border-cyan-600 shadow-lg"
                />
              </div>
            )}

            {/* Title and Tagline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-slate-900 mb-4">
              {identity?.name || 'Carlos Jiménez Hirashi'}
            </h1>
            <p className="text-xl sm:text-2xl text-cyan-600 font-semibold mb-4">
              {identity?.title || 'Solutions Architect'}
            </p>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
              {identity?.tagline ||
                'Transforming complex ideas into elegant, scalable solutions. Specialized in enterprise architecture and full-stack development.'}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/projects"
                onClick={() => handleCTA('view-portfolio')}
                className="bg-cyan-600 hover:bg-cyan-700 text-white px-8 py-3 rounded-lg font-semibold transition"
              >
                View Portfolio
              </Link>
              <Link
                to="/contact"
                onClick={() => handleCTA('contact-cta')}
                className="bg-slate-200 hover:bg-slate-300 text-slate-900 px-8 py-3 rounded-lg font-semibold transition"
              >
                Get in Touch
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="mx-auto max-w-4xl">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-cyan-600 mb-2">10+</div>
              <p className="text-slate-600">Years of Experience</p>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-cyan-600 mb-2">50+</div>
              <p className="text-slate-600">Projects Completed</p>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-cyan-600 mb-2">
                {competencies?.length || '20'}+
              </div>
              <p className="text-slate-600">Technical Skills</p>
            </div>
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">Why Work With Me</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                title: 'Expert Architecture',
                description: 'Design scalable, maintainable systems that grow with your business.',
              },
              {
                title: 'Full-Stack Expertise',
                description: 'End-to-end solutions from database design to frontend optimization.',
              },
              {
                title: 'Problem Solver',
                description: 'Transform complex challenges into elegant, practical solutions.',
              },
            ].map((item, index) => (
              <div key={index} className="bg-white p-6 rounded-lg border border-slate-200">
                <h3 className="font-bold text-lg text-slate-900 mb-2">{item.title}</h3>
                <p className="text-slate-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Projects */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="mx-auto max-w-6xl">
          <div className="flex justify-between items-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900">Featured Projects</h2>
            <Link to="/projects" className="text-cyan-600 hover:text-cyan-700 font-semibold">
              View All →
            </Link>
          </div>

          {projectsLoading && <LoadingSpinner />}
          {projectsError && <ErrorMessage message="Failed to load projects" />}

          {featuredProjects && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {featuredProjects.map(project => (
                <ProjectCard key={project.id} project={project} featured />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-cyan-600 to-cyan-700">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to work together?</h2>
          <p className="text-cyan-100 mb-8">
            Let's discuss how I can help transform your next project into reality.
          </p>
          <Link
            to="/contact"
            onClick={() => handleCTA('footer-cta')}
            className="inline-block bg-white text-cyan-600 hover:bg-slate-100 px-8 py-3 rounded-lg font-semibold transition"
          >
            Start a Conversation
          </Link>
        </div>
      </section>
    </div>
  )
}
