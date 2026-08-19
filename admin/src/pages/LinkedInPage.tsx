import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CheckCircle2, ExternalLink, Linkedin, Unlink } from 'lucide-react'
import { useLinkedInStatus, useLinkedInPosts, useLinkedInMutations } from '@/hooks/useLinkedIn'
import { linkedinApi } from '@/api/linkedin'
import { getErrorMessage } from '@/utils/errors'
import { formatDateTime } from '@/utils/formatters'
import { LoadingSpinner } from '@/components/LoadingSpinner'

const POST_MAX_LENGTH = 3000

export const LinkedInPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: status, isLoading: statusLoading, isError: statusError, error: statusErrorObj } = useLinkedInStatus()
  const { data: posts } = useLinkedInPosts()
  const { disconnectMutation, createPostMutation } = useLinkedInMutations()

  const [connecting, setConnecting] = useState(false)
  const [connectError, setConnectError] = useState<string | null>(null)
  const [postText, setPostText] = useState('')
  const [postError, setPostError] = useState<string | null>(null)
  const [banner, setBanner] = useState<'connected' | 'error' | null>(null)

  // The OAuth callback lands back here with a query param instead of a
  // normal in-app navigation - read it once, show a banner, then strip it
  // so a page refresh doesn't keep re-showing it.
  useEffect(() => {
    if (searchParams.get('linkedin_connected')) {
      setBanner('connected')
      setSearchParams({}, { replace: true })
    } else if (searchParams.get('linkedin_error')) {
      setBanner('error')
      setSearchParams({}, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleConnect = async () => {
    setConnectError(null)
    setConnecting(true)
    try {
      const authorizeUrl = await linkedinApi.connect()
      window.location.href = authorizeUrl
    } catch (err) {
      setConnectError(getErrorMessage(err))
      setConnecting(false)
    }
  }

  const handleDisconnect = () => {
    if (!window.confirm('¿Desconectar tu cuenta de LinkedIn? Tendrás que volver a autorizarla para publicar.')) return
    disconnectMutation.mutate()
  }

  const handlePublish = () => {
    setPostError(null)
    const text = postText.trim()
    if (!text) return
    createPostMutation.mutate(text, {
      onSuccess: () => setPostText(''),
      onError: (err) => setPostError(getErrorMessage(err)),
    })
  }

  return (
    <div className="space-y-6">
      {banner === 'connected' && (
        <div className="flex items-center gap-2 rounded-xl border border-green-200 dark:border-green-800/50 bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 text-sm px-4 py-3">
          <CheckCircle2 size={16} /> Cuenta de LinkedIn conectada correctamente.
        </div>
      )}
      {banner === 'error' && (
        <div className="text-sm rounded-xl border border-red-200 dark:border-red-800/50 bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 px-4 py-3">
          No se pudo conectar con LinkedIn. Intenta de nuevo.
        </div>
      )}

      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Linkedin size={18} className="text-[#0A66C2]" aria-hidden="true" />
          <h2 className="font-semibold text-text">LinkedIn</h2>
        </div>
        <div className="card-body">
          {statusLoading && <LoadingSpinner fullScreen={false} message="Comprobando conexión..." />}
          {statusError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(statusErrorObj)}</p>}

          {!statusLoading && !statusError && status && !status.connected && (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-text-secondary text-sm">
                No hay ninguna cuenta de LinkedIn conectada. Conéctala para poder publicar posts desde aquí.
              </p>
              {connectError && <p className="text-red-600 dark:text-red-400 text-sm w-full">{connectError}</p>}
              <button
                type="button"
                onClick={handleConnect}
                disabled={connecting}
                className="btn-primary btn-small flex items-center gap-1.5"
              >
                <Linkedin size={14} /> {connecting ? 'Redirigiendo...' : 'Conectar con LinkedIn'}
              </button>
            </div>
          )}

          {!statusLoading && !statusError && status && status.connected && (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                {status.profile_picture_url ? (
                  <img
                    src={status.profile_picture_url}
                    alt={status.member_name ?? 'LinkedIn'}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-[#0A66C2] flex items-center justify-center text-white flex-shrink-0">
                    <Linkedin size={18} />
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium text-text">{status.member_name ?? 'Cuenta conectada'}</p>
                  {status.member_email && <p className="text-xs text-text-secondary">{status.member_email}</p>}
                  {status.expires_at && (
                    <p className="text-xs text-text-muted">Conexión expira: {formatDateTime(status.expires_at)}</p>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={disconnectMutation.isPending}
                className="btn-secondary btn-small flex items-center gap-1.5"
              >
                <Unlink size={14} /> Desconectar
              </button>
            </div>
          )}
        </div>
      </div>

      {status?.connected && (
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-text">Publicar</h2>
          </div>
          <div className="card-body space-y-3">
            <textarea
              value={postText}
              onChange={(e) => setPostText(e.target.value.slice(0, POST_MAX_LENGTH))}
              placeholder="¿Qué quieres compartir en LinkedIn?"
              rows={6}
              className="input-field resize-y"
            />
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs text-text-muted">
                {postText.length} / {POST_MAX_LENGTH}
              </span>
              {postError && <p className="text-red-600 dark:text-red-400 text-sm flex-1">{postError}</p>}
              <button
                type="button"
                onClick={handlePublish}
                disabled={!postText.trim() || createPostMutation.isPending}
                className="btn-primary btn-small flex items-center gap-1.5"
              >
                <Linkedin size={14} /> {createPostMutation.isPending ? 'Publicando...' : 'Publicar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {status?.connected && posts && posts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-text">Publicados desde este panel</h2>
          </div>
          <div className="card-body divide-y divide-border">
            {posts.map((post) => (
              <div key={post.id} className="py-3 first:pt-0 last:pb-0">
                <p className="text-sm text-text whitespace-pre-wrap line-clamp-3">{post.text}</p>
                <div className="flex items-center gap-3 mt-1.5">
                  <span className="text-xs text-text-muted">{formatDateTime(post.published_at)}</span>
                  {post.linkedin_post_urn && (
                    <a
                      href={`https://www.linkedin.com/feed/update/${post.linkedin_post_urn}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      Ver en LinkedIn <ExternalLink size={11} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default LinkedInPage
