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
    <div className="min-h-screen bg-gradient-to-br from-cyan-50/40 to-slate-50/40 dark:from-slate-900/40 dark:to-slate-950/40">
      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl hero-split">
          {/* Copy column */}
          <div className="text-center content:text-left">
            <div className="mb-6 flex flex-wrap gap-2 justify-center content:justify-start">
              <span className="badge">Available for opportunities</span>
              <span className="badge badge-secondary">Remote-first</span>
            </div>

            {/* Title and Tagline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-text mb-4">
              {identity?.name || 'Carlos Jiménez Hirashi'}
            </h1>
            <p className="text-xl sm:text-2xl text-primary font-semibold mb-4">
              {identity?.title || 'Solutions Architect'}
            </p>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto content:mx-0 mb-8">
              {identity?.tagline ||
                'Transforming complex ideas into elegant, scalable solutions. Specialized in enterprise architecture and full-stack development.'}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center content:justify-start">
              <Link
                to="/projects"
                onClick={() => handleCTA('view-portfolio')}
                className="btn px-8 py-3 font-semibold"
              >
                View Portfolio
              </Link>
              <Link
                to="/contact"
                onClick={() => handleCTA('contact-cta')}
                className="btn-secondary px-8 py-3 font-semibold"
              >
                Get in Touch
              </Link>
            </div>
          </div>

          {/* Visual column */}
          <div className="flex justify-center content:justify-end">
            <div className="card p-8 w-full max-w-sm">
              {identity?.avatar && (
                <div className="mb-6 flex justify-center">
                  <img
                    src={identity.avatar}
                    alt={identity.name}
                    className="w-24 h-24 rounded-full border-4 border-primary shadow-glow"
                  />
                </div>
              )}
              <p className="text-center text-text-secondary text-sm mono">
                {identity?.location || 'Remote'}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="card text-center p-6">
              <div className="text-4xl font-bold text-primary mb-2">10+</div>
              <p className="text-text-secondary">Years of Experience</p>
            </div>
            <div className="card text-center p-6">
              <div className="text-4xl font-bold text-primary mb-2">50+</div>
              <p className="text-text-secondary">Projects Completed</p>
            </div>
            <div className="card text-center p-6">
              <div className="text-4xl font-bold text-primary mb-2">
                {competencies?.length || '20'}+
              </div>
              <p className="text-text-secondary">Technical Skills</p>
            </div>
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="section-alt py-16 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-3xl font-bold text-text text-center mb-12">Why Work With Me</h2>

          <div className="grid grid-cols-1 content:grid-cols-3 gap-6">
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
              <div key={index} className="card p-6">
                <h3 className="font-bold text-lg text-text mb-2">{item.title}</h3>
                <p className="text-text-secondary">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Projects */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="flex justify-between items-center mb-12">
            <h2 className="text-3xl font-bold text-text">Featured Projects</h2>
            <Link
              to="/projects"
              className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
            >
              View All →
            </Link>
          </div>

          {projectsLoading && <LoadingSpinner />}
          {projectsError && <ErrorMessage message="Failed to load projects" />}

          {featuredProjects && (
            <div className="grid grid-cols-1 content:grid-cols-3 gap-6">
              {featuredProjects.map(project => (
                <ProjectCard key={project.id} project={project} featured />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="section-alt py-16 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold text-text mb-4">Ready to work together?</h2>
          <p className="text-text-secondary mb-8">
            Let's discuss how I can help transform your next project into reality.
          </p>
          <Link
            to="/contact"
            onClick={() => handleCTA('footer-cta')}
            className="btn inline-flex px-8 py-3 font-semibold"
          >
            Start a Conversation
          </Link>
        </div>
      </section>
    </div>
  )
}
