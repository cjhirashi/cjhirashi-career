import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, GitFork, Star } from 'lucide-react'
import { careerApi } from '@/api/career'
import { getErrorMessage } from '@/utils/errors'
import { LoadingSpinner } from '@/components/LoadingSpinner'

/** Live view of a GitHub username's public repos (career/github-profile/repos)
 * - no stored data, fetched straight from GitHub's public API every time this
 * mounts. Only rendered when viewing the "github-profile" singleton record
 * (see CareerResourceView.tsx). */
export const GitHubReposPanel: React.FC = () => {
  const { data: repos, isLoading, isError, error } = useQuery({
    queryKey: ['github-repos'],
    queryFn: () => careerApi.githubRepos(),
    retry: false,
  })

  return (
    <div className="pt-4 border-t border-border">
      <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
        Repositorios (en vivo desde GitHub)
      </h3>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando repositorios..." />}
      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}
      {!isLoading && !isError && (!repos || repos.length === 0) && (
        <p className="text-text-secondary text-sm">No se encontraron repositorios públicos.</p>
      )}

      {repos && repos.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {repos.map((repo) => (
            <a
              key={repo.name}
              href={repo.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-3 rounded-xl border border-border hover:bg-glass transition-colors"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-text truncate flex items-center gap-1">
                  {repo.name}
                  <ExternalLink size={11} className="flex-shrink-0 text-text-muted" />
                </span>
                {repo.is_fork && <span className="badge badge-slate flex-shrink-0">Fork</span>}
              </div>
              {repo.description && (
                <p className="text-xs text-text-secondary mt-1 line-clamp-2">{repo.description}</p>
              )}
              <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
                {repo.language && <span>{repo.language}</span>}
                <span className="flex items-center gap-1">
                  <Star size={11} /> {repo.stars}
                </span>
                <span className="flex items-center gap-1">
                  <GitFork size={11} /> {repo.forks}
                </span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

export default GitHubReposPanel
