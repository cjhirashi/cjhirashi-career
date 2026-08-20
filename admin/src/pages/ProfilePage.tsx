import React, { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { filesApi } from '@/api/files'

export const ProfilePage: React.FC = () => {
  const { user, updateProfile, isLoading, error, clearError } = useAuth()
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [photoPreview, setPhotoPreview] = useState<string | null>(user?.photo_url ?? null)
  const [uploading, setUploading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoFile(file)
    setPhotoPreview(URL.createObjectURL(file))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setSuccess(false)

    try {
      let photoUrl = user?.photo_url ?? undefined

      if (photoFile) {
        setUploading(true)
        const uploaded = await filesApi.upload(photoFile, { category: 'perfil', isPublic: true })
        photoUrl = uploaded.download_url ?? undefined
        setUploading(false)
      }

      await updateProfile({ full_name: fullName, photo_url: photoUrl })
      setPhotoFile(null)
      setSuccess(true)
    } catch {
      setUploading(false)
      // Error is handled by useAuth hook
    }
  }

  const busy = isLoading || uploading

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Mi Perfil</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">Actualiza tu nombre y foto de perfil</p>
      </div>

      <div className="card max-w-md">
        <div className="card-body">
          {success && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800/50 rounded-lg">
              <p className="text-green-800 dark:text-green-300 text-sm font-medium">Perfil actualizado correctamente</p>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg">
              <p className="text-red-800 dark:text-red-300 text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="form-group">
              <label className="form-label">Foto de perfil</label>
              <div className="flex items-center gap-4">
                {photoPreview ? (
                  <img
                    src={photoPreview}
                    alt="Foto de perfil"
                    className="w-16 h-16 rounded-full object-cover shadow-glow flex-shrink-0"
                  />
                ) : (
                  <div className="w-16 h-16 bg-cyan-600 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-glow flex-shrink-0">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                )}
                <label className="btn-secondary cursor-pointer">
                  Cambiar foto
                  <input type="file" accept="image/*" onChange={handlePhotoChange} disabled={busy} className="hidden" />
                </label>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="fullName" className="form-label">
                Nombre completo
              </label>
              <input
                type="text"
                id="fullName"
                name="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={busy}
                className="input-field"
                placeholder="Tu nombre completo"
              />
            </div>

            <button type="submit" disabled={busy} className="btn-primary w-full">
              {uploading ? 'Subiendo foto...' : isLoading ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
