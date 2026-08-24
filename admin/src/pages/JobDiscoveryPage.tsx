import React, { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ExternalLink, Search } from 'lucide-react'
import { careerApi } from '@/api/career'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'
import { JobListing, TargetRole } from '@/types/career'

const listingKey = (listing: JobListing): string => `${listing.source}::${listing.vacancy_url}`

export const JobDiscoveryPage: React.FC = () => {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('Mexico')
  const [remote, setRemote] = useState(false)
  const [includeBoards, setIncludeBoards] = useState(false)
  const [selectedProviders, setSelectedProviders] = useState<string[]>([])
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set())
  const [importUrl, setImportUrl] = useState('')
  const [imported, setImported] = useState<JobListing | null>(null)

  const providersQuery = useQuery({
    queryKey: ['job-providers'],
    queryFn: () => careerApi.listJobProviders(),
  })

  const rolesQuery = useQuery({
    queryKey: ['target-roles'],
    queryFn: () => careerApi.list<TargetRole>('target-roles', { limit: 20, sortBy: 'priority_order' }),
  })

  const marketProviders = useMemo(
    () => (providersQuery.data ?? []).filter((p) => p.id !== 'company_boards'),
    [providersQuery.data]
  )

  const enabledIds = useMemo(
    () => marketProviders.filter((p) => p.enabled).map((p) => p.id),
    [marketProviders]
  )

  const activeProviders = selectedProviders.length > 0 ? selectedProviders : enabledIds

  const runMutation = useMutation({
    mutationFn: () =>
      careerApi.runJobDiscovery({
        query: query.trim() || undefined,
        location: location.trim() || undefined,
        providers: activeProviders,
        include_company_boards: includeBoards,
        remote,
      }),
    onSuccess: () => setSelectedKeys(new Set()),
  })

  const importMutation = useMutation({
    mutationFn: () => careerApi.importJobUrl(importUrl.trim()),
    onSuccess: (listing) => {
      setImported(listing)
      if (listing.listing_kind === 'job') {
        setSelectedKeys((prev) => new Set(prev).add(listingKey(listing)))
      }
    },
  })

  const listings = useMemo(() => {
    const fromRun = runMutation.data?.listings ?? []
    if (!imported) return fromRun
    if (fromRun.some((item) => item.vacancy_url === imported.vacancy_url)) return fromRun
    return [imported, ...fromRun]
  }, [imported, runMutation.data])

  const savable = listings.filter((item) => item.listing_kind === 'job' && selectedKeys.has(listingKey(item)))

  const saveMutation = useMutation({
    mutationFn: () => careerApi.saveJobListings(savable),
    onSuccess: () => setSelectedKeys(new Set()),
  })

  const toggleProvider = (id: string, enabled: boolean) => {
    if (!enabled) return
    setSelectedProviders((current) => {
      const base = current.length > 0 ? current : enabledIds
      return base.includes(id) ? base.filter((item) => item !== id) : [...base, id]
    })
  }

  const toggleListing = (listing: JobListing) => {
    if (listing.listing_kind !== 'job' || listing.already_saved) return
    const key = listingKey(listing)
    setSelectedKeys((current) => {
      const next = new Set(current)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const grouped = useMemo(() => {
    const map = new Map<string, JobListing[]>()
    for (const listing of listings) {
      const bucket = map.get(listing.source) ?? []
      bucket.push(listing)
      map.set(listing.source, bucket)
    }
    return map
  }, [listings])

  const defaultRole = rolesQuery.data?.[0]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Descubrir vacantes</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">
          Busca en Indeed (vía Adzuna), Get on Board, Remotive y RemoteOK. LinkedIn solo arma la
          búsqueda oficial: abre el link e importa cada <code>jobs/view</code>.
          {defaultRole?.role_name ? ` Rol objetivo: ${defaultRole.role_name}.` : ''}
        </p>
      </div>

      <form
        className="card mb-6 space-y-4"
        onSubmit={(event) => {
          event.preventDefault()
          runMutation.mutate()
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <span className="text-sm text-text-secondary">Consulta</span>
            <input
              className="mt-1 w-full rounded-xl border border-border bg-transparent px-3 py-2"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={defaultRole?.role_name || 'Backend engineer'}
            />
          </label>
          <label className="block">
            <span className="text-sm text-text-secondary">Ubicación</span>
            <input
              className="mt-1 w-full rounded-xl border border-border bg-transparent px-3 py-2"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Mexico"
            />
          </label>
        </div>

        <fieldset className="flex flex-wrap gap-3">
          <legend className="text-sm text-text-secondary mb-1">Portales</legend>
          {providersQuery.isLoading && <LoadingSpinner fullScreen={false} message="Cargando portales..." />}
          {marketProviders.map((provider) => (
            <label
              key={provider.id}
              className={`inline-flex items-center gap-2 text-sm ${provider.enabled ? '' : 'opacity-50'}`}
            >
              <input
                type="checkbox"
                checked={activeProviders.includes(provider.id)}
                disabled={!provider.enabled}
                onChange={() => toggleProvider(provider.id, provider.enabled)}
              />
              {provider.label}
              {!provider.enabled && provider.reason ? ` (${provider.reason})` : ''}
            </label>
          ))}
        </fieldset>

        <div className="flex flex-wrap gap-4 text-sm">
          <label className="inline-flex items-center gap-2">
            <input type="checkbox" checked={remote} onChange={(e) => setRemote(e.target.checked)} />
            Preferir remoto
          </label>
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeBoards}
              onChange={(e) => setIncludeBoards(e.target.checked)}
            />
            Incluir boards de empresas diana
          </label>
        </div>

        <button type="submit" className="btn-primary inline-flex items-center gap-2" disabled={runMutation.isPending}>
          <Search size={16} aria-hidden="true" />
          {runMutation.isPending ? 'Buscando…' : 'Buscar'}
        </button>
        {runMutation.isError && (
          <p className="text-error-text text-sm">{getErrorMessage(runMutation.error)}</p>
        )}
      </form>

      <form
        className="card mb-6 flex flex-col md:flex-row gap-3 md:items-end"
        onSubmit={(event) => {
          event.preventDefault()
          if (importUrl.trim()) importMutation.mutate()
        }}
      >
        <label className="block flex-1">
          <span className="text-sm text-text-secondary">Importar URL de vacante</span>
          <input
            className="mt-1 w-full rounded-xl border border-border bg-transparent px-3 py-2"
            value={importUrl}
            onChange={(e) => setImportUrl(e.target.value)}
            placeholder="https://www.linkedin.com/jobs/view/…"
          />
        </label>
        <button type="submit" className="btn-secondary" disabled={importMutation.isPending || !importUrl.trim()}>
          {importMutation.isPending ? 'Importando…' : 'Importar'}
        </button>
      </form>
      {importMutation.isError && (
        <p className="text-error-text text-sm mb-4">{getErrorMessage(importMutation.error)}</p>
      )}

      {runMutation.data?.errors?.length ? (
        <div className="mb-4 text-sm text-warning-text">
          {runMutation.data.errors.map((err) => (
            <p key={`${err.provider}-${err.message}`}>
              {err.provider}: {err.message}
            </p>
          ))}
        </div>
      ) : null}

      {listings.length > 0 && (
        <div className="mb-4 flex items-center justify-between gap-3">
          <p className="text-sm text-text-secondary">{savable.length} vacantes seleccionadas</p>
          <button
            type="button"
            className="btn-primary"
            disabled={savable.length === 0 || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? 'Guardando…' : 'Guardar seleccionadas'}
          </button>
        </div>
      )}
      {saveMutation.isSuccess && (
        <p className="text-success-text text-sm mb-4">
          Guardadas: {saveMutation.data.created.length}. Omitidas: {saveMutation.data.skipped.length}.
        </p>
      )}
      {saveMutation.isError && (
        <p className="text-error-text text-sm mb-4">{getErrorMessage(saveMutation.error)}</p>
      )}

      {Array.from(grouped.entries()).map(([source, items]) => (
        <section key={source} className="card mb-4">
          <h2 className="text-lg font-semibold mb-3 capitalize">{source}</h2>
          <ul className="space-y-3">
            {items.map((listing) => {
              const key = listingKey(listing)
              const isSearch = listing.listing_kind === 'search_url'
              return (
                <li key={key} className="flex items-start gap-3 border-b border-border last:border-0 pb-3 last:pb-0">
                  {!isSearch && (
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={selectedKeys.has(key)}
                      disabled={listing.already_saved}
                      onChange={() => toggleListing(listing)}
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{listing.exact_role}</p>
                    <p className="text-sm text-text-secondary">
                      {listing.company}
                      {listing.location ? ` · ${listing.location}` : ''}
                      {listing.already_saved ? ' · ya guardada' : ''}
                      {listing.via ? ` · vía ${listing.via}` : ''}
                    </p>
                    {listing.snippet && <p className="text-sm mt-1">{listing.snippet}</p>}
                    <a
                      href={listing.vacancy_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-primary mt-1"
                    >
                      <ExternalLink size={13} aria-hidden="true" />
                      {isSearch ? 'Abrir búsqueda en LinkedIn' : 'Abrir vacante'}
                    </a>
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      ))}

      {runMutation.isSuccess && listings.length === 0 && (
        <p className="text-text-secondary text-sm">No hubo resultados. Prueba otra consulta o portal.</p>
      )}
    </div>
  )
}
