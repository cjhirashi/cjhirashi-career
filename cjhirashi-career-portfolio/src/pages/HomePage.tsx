import { Link } from 'react-router-dom'
import { BookOpen, Layers, ShieldCheck, Sparkles } from 'lucide-react'
import { useHome } from '@/hooks/useHome'
import { useTrackClick } from '@/hooks/useTracking'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { BlogCard } from '@/components/Common/BlogCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { Markdown } from '@/components/Common/Markdown'

export const HomePage = () => {
  const { data: home, isLoading, error } = useHome()
  const { trackClick } = useTrackClick()

  const handleCTA = (action: string) => {
    trackClick(`hero-${action}`)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudo cargar el contenido de la Home" />

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50/40 to-slate-50/40 dark:from-slate-900/40 dark:to-slate-950/40">
      {/* Hero - single centered column: photo, role badge, headline, tagline, CTAs, over the animated SVG background */}
      <section data-theme="dark" className="hero-animated py-20 px-4 sm:px-6 lg:px-8 text-center">
        <div className="mx-auto max-w-3xl flex flex-col items-center">
          {home?.hero_photo_url && (
            <img
              src={home.hero_photo_url}
              alt="Carlos A. Jiménez Hirashi"
              className="w-48 h-48 sm:w-56 sm:h-56 rounded-full object-cover border-4 border-primary shadow-glow mb-6"
            />
          )}

          {home?.hero_subtitle && (
            <span className="badge mb-6 flex items-center gap-1.5 text-sm">
              <ShieldCheck size={14} /> {home.hero_subtitle}
            </span>
          )}

          {home?.hero_title && (
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-text mb-6">
              {home.hero_title}
            </h1>
          )}

          {home?.hero_intro && (
            <Markdown className="text-lg max-w-xl mb-8">{home.hero_intro}</Markdown>
          )}

          {home && home.hero_ctas.length > 0 && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {home.hero_ctas.map((cta, index) => {
                const className = index === 0 ? 'btn px-8 py-3 font-semibold' : 'btn-secondary px-8 py-3 font-semibold'
                const onClick = () => handleCTA(`cta-${index}-${cta.label}`)
                return cta.url.startsWith('/') ? (
                  <Link key={cta.label} to={cta.url} onClick={onClick} className={className}>
                    {cta.label}
                  </Link>
                ) : (
                  <a
                    key={cta.label}
                    href={cta.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={onClick}
                    className={className}
                  >
                    {cta.label}
                  </a>
                )
              })}
            </div>
          )}
        </div>
      </section>

      {/* Stats */}
      {home && home.stats.length > 0 && (
        <section className="py-14 px-4 sm:px-6 lg:px-8 border-t border-border">
          <div className="mx-auto max-w-4xl grid grid-cols-2 sm:grid-cols-4 divide-x divide-border">
            {home.stats.map(stat => (
              <div key={stat.label} className="text-center px-4">
                <div className="text-3xl font-bold mb-1 text-primary">{stat.value}</div>
                <p className="text-text-secondary text-xs uppercase tracking-wide">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Stack técnico - the competencies marked featured_on_home, grouped
          by category (see api/src/routes/public.py's get_home); the full
          skill breakdown lives on About. */}
      {home && home.skill_groups.length > 0 && (
        <section className="section-alt py-24 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-bold text-text flex items-center justify-center gap-2 mb-8">
              <Layers size={22} className="text-primary" /> Stack técnico
            </h2>
            <div className="space-y-6 mb-8">
              {home.skill_groups.map(group => (
                <div key={group.category}>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-text-muted mb-3">{group.category}</h3>
                  <div className="flex flex-wrap justify-center gap-3">
                    {group.skills.map(skill => (
                      <span key={skill} className="badge mono">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <Link
              to="/about"
              onClick={() => trackClick('home-ver-stack-completo')}
              className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
            >
              Ver más en Sobre Mí →
            </Link>
          </div>
        </section>
      )}

      {/* Habilidades - featured transferable competencies, separate from the
          technical stack. */}
      {home && home.soft_skills.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-bold text-text flex items-center justify-center gap-2 mb-8">
              <Sparkles size={22} className="text-primary" /> Habilidades
            </h2>
            <div className="flex flex-wrap justify-center gap-3">
              {home.soft_skills.map(skill => (
                <span key={skill} className="badge">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Projects */}
      {home && home.featured_projects.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="flex justify-between items-center mb-12">
              <h2 className="text-3xl font-bold text-text">Proyectos</h2>
              <Link
                to="/projects"
                className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
              >
                Ver todos →
              </Link>
            </div>

            <div className="grid grid-cols-1 content:grid-cols-3 gap-6">
              {home.featured_projects.map(project => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Publications */}
      {home && home.featured_publications.length > 0 && (
        <section className="section-alt py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="flex justify-between items-center mb-12">
              <h2 className="text-3xl font-bold text-text flex items-center gap-2">
                <BookOpen size={22} className="text-primary" /> Del blog
              </h2>
              <Link
                to="/blog"
                className="text-primary hover:[text-shadow:0_0_10px_var(--primary-glow)] font-semibold"
              >
                Ver todos →
              </Link>
            </div>

            <div className="grid grid-cols-1 content:grid-cols-3 gap-6">
              {home.featured_publications.map(post => (
                <BlogCard key={post.id} post={post} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Footer CTA */}
      <section className="section-alt py-16 px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-2xl sm:text-3xl font-bold text-text mb-6">¿Hablamos de tu próximo sistema?</h2>
        <Link to="/contact" onClick={() => trackClick('home-footer-cta')} className="btn inline-flex px-8 py-3 font-semibold">
          Hablemos
        </Link>
      </section>
    </div>
  )
}
