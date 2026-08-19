import React, { useRef, useState } from 'react'
import {
  Copy,
  Check,
  FileArchive,
  FileText,
  File as FileIcon,
  Folder,
  Globe,
  Lock,
  Trash2,
  Upload,
} from 'lucide-react'
import { useFilesList, useFileCategories, useFileMutations } from '@/hooks/useFiles'
import { filesApi } from '@/api/files'
import { FileUploadEntity } from '@/types/files'
import { getErrorMessage } from '@/utils/errors'
import { formatFileSize, formatDateTime } from '@/utils/formatters'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Modal } from '@/components/Modal'

const FileTypeIcon: React.FC<{ type: FileUploadEntity['file_type'] }> = ({ type }) => {
  if (type === 'document') return <FileText size={28} className="text-text-secondary" aria-hidden="true" />
  if (type === 'archive') return <FileArchive size={28} className="text-text-secondary" aria-hidden="true" />
  return <FileIcon size={28} className="text-text-secondary" aria-hidden="true" />
}

const FileCard: React.FC<{
  file: FileUploadEntity
  onDelete: () => void
  onToggleVisibility: () => void
  isTogglingVisibility: boolean
}> = ({ file, onDelete, onToggleVisibility, isTogglingVisibility }) => {
  const [copied, setCopied] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const isPreviewableImage = file.file_type === 'image' && file.is_public && !!file.download_url

  const handleCopyLink = () => {
    if (!file.download_url) return
    navigator.clipboard.writeText(file.download_url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  const handleViewPrivate = async () => {
    setPreviewError(null)
    try {
      const url = await filesApi.getDownloadUrl(file.id)
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      setPreviewError(getErrorMessage(err))
    }
  }

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div
        className={`aspect-video rounded-lg overflow-hidden flex items-center justify-center bg-glass ${isPreviewableImage ? 'cursor-zoom-in' : ''}`}
        onClick={isPreviewableImage ? () => setPreviewOpen(true) : undefined}
        role={isPreviewableImage ? 'button' : undefined}
        tabIndex={isPreviewableImage ? 0 : undefined}
        aria-label={isPreviewableImage ? `Ver ${file.original_filename} en grande` : undefined}
        onKeyDown={
          isPreviewableImage
            ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  setPreviewOpen(true)
                }
              }
            : undefined
        }
      >
        {isPreviewableImage ? (
          <img src={file.download_url!} alt={file.original_filename} className="w-full h-full object-cover" />
        ) : !file.is_public ? (
          <Lock size={28} className="text-text-secondary" aria-hidden="true" />
        ) : (
          <FileTypeIcon type={file.file_type} />
        )}
      </div>

      {isPreviewableImage && previewOpen && (
        <Modal title={file.original_filename} onClose={() => setPreviewOpen(false)} maxWidth="max-w-4xl">
          <img src={file.download_url!} alt={file.original_filename} className="w-full h-auto rounded-lg" />
        </Modal>
      )}

      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <p className="text-sm font-medium text-text truncate flex-1" title={file.original_filename}>
            {file.original_filename}
          </p>
          {file.category && (
            <span className="badge badge-slate flex items-center gap-1 flex-shrink-0">
              <Folder size={10} aria-hidden="true" /> {file.category}
            </span>
          )}
        </div>
        <p className="text-xs text-text-secondary">
          {formatFileSize(file.file_size)} · {formatDateTime(file.created_at)}
        </p>
        {previewError && <p className="text-red-600 dark:text-red-400 text-xs mt-1">{previewError}</p>}
      </div>

      <div className="flex items-center gap-2 mt-auto">
        {file.is_public ? (
          <button
            type="button"
            onClick={handleCopyLink}
            className="btn-secondary btn-small flex-1 flex items-center justify-center gap-1"
            disabled={!file.download_url}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? 'Copiado' : 'Copiar link'}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleViewPrivate}
            className="btn-secondary btn-small flex-1 flex items-center justify-center gap-1"
          >
            <Lock size={14} /> Ver
          </button>
        )}
        <button
          type="button"
          onClick={onToggleVisibility}
          disabled={isTogglingVisibility}
          aria-label={file.is_public ? 'Hacer privado' : 'Hacer público'}
          title={file.is_public ? 'Hacer privado' : 'Hacer público'}
          className="btn-icon flex-shrink-0"
        >
          {file.is_public ? <Globe size={16} /> : <Lock size={16} />}
        </button>
        <button
          type="button"
          onClick={onDelete}
          aria-label="Eliminar"
          title="Eliminar"
          className="btn-icon btn-icon-danger flex-shrink-0"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  )
}

export const FilesPage: React.FC = () => {
  const [categoryFilter, setCategoryFilter] = useState('')
  const [uploadCategory, setUploadCategory] = useState('')
  const [uploadIsPublic, setUploadIsPublic] = useState(true)
  const { data, isLoading, isError, error, refetch } = useFilesList(
    categoryFilter ? { category: categoryFilter } : {}
  )
  const { data: categories } = useFileCategories()
  const { uploadMutation, deleteMutation, visibilityMutation } = useFileMutations()
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setUploadError(null)
    uploadMutation.mutate(
      { file, options: { category: uploadCategory.trim() || undefined, isPublic: uploadIsPublic } },
      { onError: (err) => setUploadError(getErrorMessage(err)) }
    )
  }

  const handleDelete = (file: FileUploadEntity) => {
    if (!window.confirm(`¿Eliminar "${file.original_filename}"? Esta acción no se puede deshacer.`)) return
    deleteMutation.mutate(file.id)
  }

  return (
    <div className="card">
      <div className="card-header flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-semibold text-text">Archivos</h2>

        <div className="flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor="category-filter">
            Filtrar por carpeta
          </label>
          <select
            id="category-filter"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="input-field text-sm py-1.5 w-auto"
          >
            <option value="">Todas las carpetas</option>
            {categories?.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <input
            type="text"
            list="upload-categories"
            value={uploadCategory}
            onChange={(e) => setUploadCategory(e.target.value)}
            placeholder="Carpeta (opcional)"
            aria-label="Carpeta para el próximo archivo a subir"
            className="input-field text-sm py-1.5 w-40"
          />
          <datalist id="upload-categories">
            {categories?.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>

          <label className="flex items-center gap-1.5 text-sm text-text-secondary select-none">
            <input
              type="checkbox"
              checked={uploadIsPublic}
              onChange={(e) => setUploadIsPublic(e.target.checked)}
              className="h-4 w-4 rounded border-border text-cyan-600 focus:ring-cyan-500"
            />
            Público
          </label>

          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileSelected}
            aria-label="Seleccionar archivo"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="btn-primary btn-small flex items-center gap-1"
            disabled={uploadMutation.isPending}
          >
            <Upload size={14} /> {uploadMutation.isPending ? 'Subiendo...' : 'Subir archivo'}
          </button>
        </div>
      </div>

      <div className="card-body">
        {uploadError && <p className="text-red-600 dark:text-red-400 text-sm mb-4">{uploadError}</p>}
        {isLoading && <LoadingSpinner fullScreen={false} message="Cargando archivos..." />}

        {isError && (
          <div className="text-center py-6">
            <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>
            <button type="button" onClick={() => refetch()} className="btn-secondary btn-small mt-3">
              Reintentar
            </button>
          </div>
        )}

        {!isLoading && !isError && (data?.length ?? 0) === 0 && (
          <p className="text-text-secondary text-sm text-center py-6">
            {categoryFilter ? `No hay archivos en "${categoryFilter}".` : 'No has subido ningún archivo todavía.'}
          </p>
        )}

        {!isLoading && !isError && (data?.length ?? 0) > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data!.map((file) => (
              <FileCard
                key={file.id}
                file={file}
                onDelete={() => handleDelete(file)}
                onToggleVisibility={() =>
                  visibilityMutation.mutate({ id: file.id, isPublic: !file.is_public })
                }
                isTogglingVisibility={visibilityMutation.isPending && visibilityMutation.variables?.id === file.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default FilesPage
