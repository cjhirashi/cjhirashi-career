import React, { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ImagePlus, Upload, X } from 'lucide-react'
import { filesApi } from '@/api/files'
import { PersonAvatar } from '@/components/PersonAvatar'
import { getErrorMessage } from '@/utils/errors'

interface BucketImagePickerProps {
  value: string | null | undefined
  onChange: (url: string | null) => void
  label?: string
  name?: string
  category?: string
  disabled?: boolean
}

export const BucketImagePicker: React.FC<BucketImagePickerProps> = ({
  value,
  onChange,
  label = 'Foto',
  name = 'agente',
  category = 'agentes',
  disabled,
}) => {
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const filesQuery = useQuery({
    queryKey: ['files', 'images', category],
    queryFn: () => filesApi.list({ skip: 0, limit: 100, fileType: 'image' }),
    enabled: open,
  })
  const uploadMutation = useMutation({
    mutationFn: (file: File) => filesApi.upload(file, { category, isPublic: true }),
    onSuccess: (uploaded) => {
      queryClient.invalidateQueries({ queryKey: ['files'] })
      const url = uploaded.download_url
      if (url) onChange(url)
      setOpen(false)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const images = (filesQuery.data ?? []).filter((file) => file.file_type === 'image')

  const pickFile = async (file: (typeof images)[number]) => {
    setError(null)
    try {
      let url = file.download_url
      if (!url || !file.is_public) {
        const published = await filesApi.setVisibility(file.id, true)
        url = published.download_url
      }
      if (!url) url = await filesApi.getDownloadUrl(file.id)
      onChange(url)
      setOpen(false)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-text-secondary">
        Elige una imagen del bucket o sube una nueva (queda pública para mostrarla en tareas).
      </p>
      <div className="flex items-center gap-3">
        <PersonAvatar src={value} name={name} size={48} />
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn-secondary btn-small inline-flex items-center gap-1.5"
            disabled={disabled}
            onClick={() => setOpen((current) => !current)}
          >
            <ImagePlus size={14} aria-hidden="true" />
            {open ? 'Cerrar bucket' : `Elegir ${label.toLowerCase()} del bucket`}
          </button>
          <button
            type="button"
            className="btn-secondary btn-small inline-flex items-center gap-1.5"
            disabled={disabled || uploadMutation.isPending}
            onClick={() => inputRef.current?.click()}
          >
            <Upload size={14} aria-hidden="true" />
            {uploadMutation.isPending ? 'Subiendo…' : 'Subir imagen'}
          </button>
          {value && (
            <button
              type="button"
              className="btn-secondary btn-small inline-flex items-center gap-1.5"
              disabled={disabled}
              onClick={() => onChange(null)}
            >
              <X size={14} aria-hidden="true" />
              Quitar
            </button>
          )}
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        aria-label={`Subir ${label.toLowerCase()}`}
        onChange={(event) => {
          const file = event.target.files?.[0]
          event.target.value = ''
          if (file) {
            setError(null)
            uploadMutation.mutate(file)
          }
        }}
      />
      {open && (
        <div className="rounded-xl border border-border bg-glass/30 p-3">
          {filesQuery.isLoading && <p className="text-sm text-text-secondary">Cargando imágenes…</p>}
          {filesQuery.isError && (
            <p className="text-sm text-red-400">{getErrorMessage(filesQuery.error)}</p>
          )}
          {!filesQuery.isLoading && images.length === 0 && (
            <p className="text-sm text-text-secondary">No hay imágenes en el bucket. Sube una arriba.</p>
          )}
          {images.length > 0 && (
            <ul className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
              {images.map((file) => {
                const src = file.download_url
                const selected = Boolean(value && src && value === src)
                return (
                  <li key={file.id}>
                    <button
                      type="button"
                      className={`w-full rounded-lg overflow-hidden border ${
                        selected ? 'border-cyan-500 ring-1 ring-cyan-500' : 'border-border'
                      } bg-glass aspect-square`}
                      title={file.original_filename}
                      onClick={() => pickFile(file)}
                    >
                      {src ? (
                        <img src={src} alt={file.original_filename} className="w-full h-full object-cover" />
                      ) : (
                        <span className="flex items-center justify-center h-full text-[10px] text-text-muted px-1">
                          {file.original_filename}
                        </span>
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}
