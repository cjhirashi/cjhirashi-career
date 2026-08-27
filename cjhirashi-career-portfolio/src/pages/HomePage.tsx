import { Link } from 'react-router-dom'
import { Award, BookOpen, Clock, Layers, ShieldCheck, TrendingUp } from 'lucide-react'
import { useHome } from '@/hooks/useHome'
import { useTrackClick } from '@/hooks/useTracking'
import { ProjectCard } from '@/components/Common/ProjectCard'
import { BlogCard } from '@/components/Common/BlogCard'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { Markdown } from '@/components/Common/Markdown'
import { MetricChips } from '@/components/Common/MetricChips'
import { parseMetrics } from '@/utils/metrics'

export const HomePage = () => {
  const { data: home, isLoading, error } = useHome()
  const { trackClick } = useTrackClick()

  const handleCTA = (action: string) => {
    trackClick(`hero-${action}`)
  }

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudo cargar el contenido de la Home" />

  const achievement = home?.home_achievement
  const hasAchievementMetrics = parseMetrics(achievement?.impact_metrics).length > 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50/40 to-slate-50/40 dark:from-slate-900/40 dark:to-slate-950/40">
      {/* Hero - single centered column: photo, role badge, headline, tagline, CTAs */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 text-center">
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
        <section className="py-8 px-4 sm:px-6 lg:px-8 border-t border-border">
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

      {/* Flagship achievement - the single achievements.home=True row,
          rendered as a highlighted narrative card. Short KPI-style metrics
          live as a footer row inside the card. */}
      {achievement && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl card p-8">
            <div className="flex items-center gap-2 mb-2">
              <Award size={14} className="text-primary flex-shrink-0" />
              <span className="text-xs font-bold text-primary uppercase tracking-wide">Logro destacado</span>
            </div>
            <h2 className="text-2xl font-bold text-text mb-6">{achievement.title}</h2>

            <div className="space-y-5">
              {achievement.executive_storytelling && (
                <Markdown className="text-sm text-text-secondary">{achievement.executive_storytelling}</Markdown>
              )}

              {achievement.challenge && (
                <div>
                  <p className="text-xs font-bold text-primary uppercase tracking-wide flex items-center gap-1.5 mb-1.5">
                    <Clock size={12} /> Desafío
                  </p>
                  <Markdown className="text-sm">{achievement.challenge}</Markdown>
                </div>
              )}

              {achievement.solution && (
                <div className="rounded-lg p-4 bg-secondary-light border border-secondary-light">
                  <p className="text-xs font-bold text-secondary uppercase tracking-wide flex items-center gap-1.5 mb-1.5">
                    <TrendingUp size={12} /> Resultado
                  </p>
                  <Markdown className="text-sm">{achievement.solution}</Markdown>
                </div>
              )}
            </div>

            {hasAchievementMetrics && (
              <div className="mt-6 pt-6 border-t border-border">
                <MetricChips metrics={achievement.impact_metrics} />
              </div>
            )}
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

      {/* Stack técnico - categories of whichever competencies are marked
          featured_on_home (see api/src/routes/public.py's get_home), the
          full skill breakdown lives on About. */}
      {home && home.skill_categories.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-bold text-text flex items-center justify-center gap-2 mb-8">
              <Layers size={22} className="text-primary" /> Stack técnico
            </h2>
            <div className="flex flex-wrap justify-center gap-3 mb-6">
              {home.skill_categories.map(category => (
                <span key={category} className="badge mono">
                  {category}
                </span>
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
