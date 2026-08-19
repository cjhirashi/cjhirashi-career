import React, { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CheckCircle2, Clock, ExternalLink, Image as ImageIcon, Linkedin, Unlink, X } from 'lucide-react'
import { useLinkedInStatus, useLinkedInPosts, useLinkedInMutations } from '@/hooks/useLinkedIn'
import { linkedinApi } from '@/api/linkedin'
import { LinkedInPostEntity } from '@/types/linkedin'
import { getErrorMessage } from '@/utils/errors'
import { formatDateTime } from '@/utils/formatters'
import { LoadingSpinner } from '@/components/LoadingSpinner'

const POST_MAX_LENGTH = 3000

const PostStatusBadge: React.FC<{ post: LinkedInPostEntity }> = ({ post }) => {
  if (post.status === 'scheduled') {
    return (
      <span className="badge badge-slate flex items-center gap-1 w-fit">
        <Clock size={10} aria-hidden="true" /> Programado: {post.scheduled_at && formatDateTime(post.scheduled_at)}
      </span>
    )
  }
  if (post.status === 'failed') {
    return <span className="badge badge-error w-fit">Falló</span>
  }
  return <span className="badge badge-cyan w-fit">Publicado</span>
}

export const LinkedInPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: status, isLoading: statusLoading, isError: statusError, error: statusErrorObj } = useLinkedInStatus()
  const { data: posts } = useLinkedInPosts()
  const { disconnectMutation, createPostMutation, cancelPostMutation } = useLinkedInMutations()

  const [connecting, setConnecting] = useState(false)
  const [connectError, setConnectError] = useState<string | null>(null)
  const [postText, setPostText] = useState('')
  const [postImage, setPostImage] = useState<File | null>(null)
  const [postImagePreview, setPostImagePreview] = useState<string | null>(null)
  const [scheduleEnabled, setScheduleEnabled] = useState(false)
  const [scheduledAt, setScheduledAt] = useState('')
  const [postError, setPostError] = useState<string | null>(null)
  const [banner, setBanner] = useState<'connected' | 'error' | null>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)

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

  useEffect(() => {
    if (!postImage) {
      setPostImagePreview(null)
      return
    }
    const objectUrl = URL.createObjectURL(postImage)
    setPostImagePreview(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [postImage])

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

  const handleImageSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (file) setPostImage(file)
  }

  const handlePublish = () => {
    setPostError(null)
    const text = postText.trim()
    if (!text) return
    if (scheduleEnabled && !scheduledAt) {
      setPostError('Elige una fecha y hora para programar el post.')
      return
    }

    createPostMutation.mutate(
      {
        text,
        image: postImage ?? undefined,
        scheduledAt: scheduleEnabled ? new Date(scheduledAt).toISOString() : undefined,
      },
      {
        onSuccess: () => {
          setPostText('')
          setPostImage(null)
          setScheduleEnabled(false)
          setScheduledAt('')
        },
        onError: (err) => setPostError(getErrorMessage(err)),
      }
    )
  }

  const handleCancelScheduled = (post: LinkedInPostEntity) => {
    if (!window.confirm('¿Cancelar este post programado? No se publicará.')) return
    cancelPostMutation.mutate(post.id)
  }

  const minDateTimeLocal = new Date(Date.now() + 5 * 60 * 1000).toISOString().slice(0, 16)

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

            {postImagePreview && (
              <div className="relative w-fit">
                <img src={postImagePreview} alt="Vista previa" className="max-h-48 rounded-lg border border-border" />
                <button
                  type="button"
                  onClick={() => setPostImage(null)}
                  aria-label="Quitar imagen"
                  title="Quitar imagen"
                  className="absolute -top-2 -right-2 p-1 rounded-full bg-glass border border-border text-text-secondary hover:text-red-600"
                >
                  <X size={13} />
                </button>
              </div>
            )}

            <div className="flex flex-wrap items-center gap-4">
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleImageSelected}
                aria-label="Seleccionar imagen"
              />
              <button
                type="button"
                onClick={() => imageInputRef.current?.click()}
                className="btn-secondary btn-small flex items-center gap-1.5"
              >
                <ImageIcon size={14} /> {postImage ? 'Cambiar imagen' : 'Agregar imagen'}
              </button>

              <label className="flex items-center gap-1.5 text-sm text-text-secondary select-none">
                <input
                  type="checkbox"
                  checked={scheduleEnabled}
                  onChange={(e) => setScheduleEnabled(e.target.checked)}
                  className="h-4 w-4 rounded border-border text-cyan-600 focus:ring-cyan-500"
                />
                Programar
              </label>

              {scheduleEnabled && (
                <input
                  type="datetime-local"
                  value={scheduledAt}
                  min={minDateTimeLocal}
                  onChange={(e) => setScheduledAt(e.target.value)}
                  className="input-field text-sm py-1.5 w-auto"
                  aria-label="Fecha y hora programada"
                />
              )}
            </div>

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
                <Linkedin size={14} />
                {createPostMutation.isPending
                  ? scheduleEnabled
                    ? 'Programando...'
                    : 'Publicando...'
                  : scheduleEnabled
                    ? 'Programar'
                    : 'Publicar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {status?.connected && (
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-text">Publicados desde este panel</h2>
          </div>
          <div className="card-body">
            {(!posts || posts.length === 0) && (
              <p className="text-text-secondary text-sm text-center py-6">
                Aún no has publicado ni programado nada desde aquí.
              </p>
            )}
            {posts && posts.length > 0 && (
              <div className="divide-y divide-border">
                {posts.map((post) => (
              <div key={post.id} className="py-3 first:pt-0 last:pb-0 flex gap-3">
                {post.image_url && (
                  <img src={post.image_url} alt="" className="w-16 h-16 rounded-lg object-cover flex-shrink-0" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-text whitespace-pre-wrap line-clamp-3">{post.text}</p>
                  {post.status === 'failed' && post.error_message && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">{post.error_message}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-3 mt-1.5">
                    <PostStatusBadge post={post} />
                    <span className="text-xs text-text-muted">{formatDateTime(post.created_at)}</span>
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
                    {post.status === 'scheduled' && (
                      <button
                        type="button"
                        onClick={() => handleCancelScheduled(post)}
                        disabled={cancelPostMutation.isPending}
                        className="text-xs text-red-600 dark:text-red-400 hover:underline"
                      >
                        Cancelar
                      </button>
                    )}
                  </div>
                </div>
              </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default LinkedInPage
