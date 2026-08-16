import { useIdentity, useCompetencies } from '@/hooks/useIdentity'
import { LoadingSpinner } from '@/components/Common/LoadingSpinner'
import { ErrorMessage } from '@/components/Common/ErrorMessage'

export const AboutPage = () => {
  const { data: identity, isLoading, error } = useIdentity()
  const { data: competencies } = useCompetencies()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="Failed to load profile" />

  return (
    <div className="min-h-screen py-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">About Me</h1>
          <p className="text-lg text-slate-600">{identity?.bio}</p>
        </div>

        {/* Avatar and Quick Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-16">
          {/* Photo */}
          <div className="md:col-span-1">
            {identity?.avatar && (
              <div className="sticky top-20">
                <img
                  src={identity.avatar}
                  alt={identity.name}
                  className="w-full rounded-lg shadow-lg border-4 border-cyan-600"
                />
                <div className="mt-6 bg-cyan-50 p-4 rounded-lg">
                  <h3 className="font-bold text-slate-900 mb-2">{identity.name}</h3>
                  <p className="text-cyan-600 font-semibold">{identity.title}</p>
                  <p className="text-slate-600 text-sm mt-2">{identity.location}</p>
                </div>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="md:col-span-2 space-y-8">
            {/* IKIGAI */}
            {identity?.ikigai && (
              <div>
                <h2 className="text-2xl font-bold text-slate-900 mb-4">My IKIGAI</h2>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(identity.ikigai).map(([key, value]) => (
                    <div key={key} className="bg-cyan-50 p-4 rounded-lg">
                      <p className="text-xs uppercase font-bold text-cyan-700 mb-2">
                        {key.replace(/_/g, ' ')}
                      </p>
                      <p className="text-slate-900">{value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Core Values */}
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4">Core Values</h2>
              <ul className="space-y-3">
                {[
                  'Excellence in technical delivery',
                  'Continuous learning and growth',
                  'Collaboration and communication',
                  'Ethical and sustainable solutions',
                ].map((value, index) => (
                  <li key={index} className="flex items-start">
                    <svg
                      className="w-5 h-5 text-cyan-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-slate-700">{value}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Competencies */}
        {competencies && competencies.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-slate-900 mb-8">Technical Skills</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {competencies.map((skill, index) => (
                <div key={index} className="bg-slate-50 border border-slate-200 px-4 py-3 rounded-lg">
                  <p className="text-slate-700 font-medium text-sm">{skill}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Timeline */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 mb-8">Experience</h2>
          <div className="space-y-6">
            {[
              {
                year: '2020-Present',
                title: 'Senior Solutions Architect',
                company: 'Tech Company',
                description: 'Leading architecture and design of enterprise-scale applications',
              },
              {
                year: '2018-2020',
                title: 'Full-Stack Developer',
                company: 'Web Agency',
                description: 'Developed and maintained multiple client projects using modern stack',
              },
              {
                year: '2015-2018',
                title: 'Junior Developer',
                company: 'Startup',
                description: 'Started career building web applications and learning modern development practices',
              },
            ].map((item, index) => (
              <div key={index} className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-3 h-3 rounded-full bg-cyan-600 mt-2"></div>
                </div>
                <div className="flex-grow pb-6 border-l border-slate-200 pl-6">
                  <p className="text-sm font-bold text-cyan-600">{item.year}</p>
                  <h3 className="text-lg font-bold text-slate-900">{item.title}</h3>
                  <p className="text-slate-600">{item.company}</p>
                  <p className="text-slate-600 text-sm mt-1">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
