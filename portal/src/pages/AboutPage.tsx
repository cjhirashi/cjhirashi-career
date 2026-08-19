import { useAbout } from '@/hooks/useAbout'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'
import { format, parseISO } from 'date-fns'

const formatMonthYear = (value: string | null) => {
  if (!value) return 'Presente'
  try {
    return format(parseISO(value), 'MMM yyyy')
  } catch {
    return value
  }
}

const ikigaiLabels: Record<string, string> = {
  passion: 'Pasión',
  profession: 'Profesión',
  vocation: 'Vocación',
  mission: 'Misión',
}

export const AboutPage = () => {
  const { data: about, isLoading, error } = useAbout()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="No se pudo cargar el contenido de Sobre Mí" />

  const highlightedCompetencies = about?.competencies.filter(c => c.is_highlighted) ?? []
  const otherCompetencies = about?.competencies.filter(c => !c.is_highlighted) ?? []

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text mb-4">Sobre Mí</h1>
          {about?.professional_tagline && (
            <p className="text-lg text-primary font-semibold">{about.professional_tagline}</p>
          )}
        </div>

        <div className="grid grid-cols-1 content:grid-cols-3 gap-12 mb-16">
          {/* Photo + quick info */}
          <div className="content:col-span-1">
            <div className="sticky top-20 card p-4">
              {about?.photo_url && (
                <img
                  src={about.photo_url}
                  alt="Carlos Jiménez Hirashi"
                  className="w-full rounded-md shadow-glow border-4 border-primary mb-4"
                />
              )}
              {about?.personal_quote && (
                <p className="text-text-secondary text-sm italic">"{about.personal_quote}"</p>
              )}
            </div>
          </div>

          {/* Bio / UVP / IKIGAI */}
          <div className="content:col-span-2 space-y-8">
            {about?.bio_summary && (
              <div>
                <h2 className="text-2xl font-bold text-text mb-4">Mi historia</h2>
                <p className="text-text-secondary whitespace-pre-wrap">{about.bio_summary}</p>
              </div>
            )}

            {about?.unique_value_proposition && (
              <div>
                <h2 className="text-2xl font-bold text-text mb-4">Propuesta de valor</h2>
                <p className="text-text-secondary whitespace-pre-wrap">{about.unique_value_proposition}</p>
              </div>
            )}

            {about && about.ikigai.length > 0 && (
              <div>
                <h2 className="text-2xl font-bold text-text mb-4">Mi IKIGAI</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {about.ikigai.map(item => (
                    <div key={item.dimension} className="card p-4">
                      <p className="text-xs uppercase font-bold text-primary mb-2">
                        {ikigaiLabels[item.dimension] ?? item.dimension}
                      </p>
                      <p className="text-text text-sm whitespace-pre-wrap">{item.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {about && about.values.length > 0 && (
              <div>
                <h2 className="text-2xl font-bold text-text mb-4">Valores</h2>
                <ul className="space-y-2">
                  {about.values.map((value, index) => (
                    <li key={index} className="flex items-start">
                      <svg
                        className="w-5 h-5 text-primary mr-3 mt-0.5 flex-shrink-0"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span className="text-text-secondary">{value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {about && about.interests_hobbies.length > 0 && (
              <div>
                <h2 className="text-2xl font-bold text-text mb-4">Intereses</h2>
                <div className="flex flex-wrap gap-2">
                  {about.interests_hobbies.map((item, index) => (
                    <span key={index} className="badge">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Skills */}
        {about && about.competencies.length > 0 && (
          <section className="section-alt -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-12 mb-16">
            <h2 className="text-2xl font-bold text-text mb-8">Habilidades Técnicas</h2>
            {highlightedCompetencies.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {highlightedCompetencies.map(skill => (
                  <span key={skill.name} className="badge mono">
                    {skill.name}
                  </span>
                ))}
              </div>
            )}
            {otherCompetencies.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {otherCompetencies.map(skill => (
                  <span key={skill.name} className="badge badge-secondary mono">
                    {skill.name}
                  </span>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Certifications */}
        {about && about.certifications.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-text mb-8">Certificaciones</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {about.certifications.map((cert, index) => (
                <div key={index} className="card p-4">
                  <h3 className="font-bold text-text">{cert.name}</h3>
                  <p className="text-text-secondary text-sm">
                    {[cert.institution, cert.year].filter(Boolean).join(' · ')}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Timeline */}
        {about && about.work_history.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-text mb-8">Experiencia</h2>
            <div className="space-y-6">
              {about.work_history.map((item, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-3 h-3 rounded-full bg-cyan-600 shadow-glow mt-2"></div>
                  </div>
                  <div className="flex-grow pb-6 border-l border-border pl-6">
                    <p className="text-sm font-bold text-primary mono">
                      {formatMonthYear(item.start_date)} - {formatMonthYear(item.end_date)}
                    </p>
                    <h3 className="text-lg font-bold text-text">{item.role_title}</h3>
                    <p className="text-text-secondary">{item.company}</p>
                    {item.description && (
                      <p className="text-text-secondary text-sm mt-1 whitespace-pre-wrap">{item.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
