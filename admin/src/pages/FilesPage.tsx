import React, { useRef, useState } from 'react'
import {
  Copy,
  Check,
  Download,
  Eye,
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
  if (type === 'document') return <FileText size={18} className="text-text-secondary" aria-hidden="true" />
  if (type === 'archive') return <FileArchive size={18} className="text-text-secondary" aria-hidden="true" />
  return <FileIcon size={18} className="text-text-secondary" aria-hidden="true" />
}

const FileRow: React.FC<{
  file: FileUploadEntity
  onDelete: () => void
  onToggleVisibility: () => void
  isTogglingVisibility: boolean
  onPreviewImage: (url: string) => void
}> = ({ file, onDelete, onToggleVisibility, isTogglingVisibility, onPreviewImage }) => {
  const [copied, setCopied] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const handleDownload = async () => {
    setDownloadError(null)
    setDownloading(true)
    try {
      const blob = await filesApi.downloadBlob(file.id)
      const objectUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = file.original_filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(objectUrl)
    } catch (err) {
      setDownloadError(getErrorMessage(err))
    } finally {
      setDownloading(false)
    }
  }

  const handleCopyLink = () => {
    if (!file.download_url) return
    navigator.clipboard.writeText(file.download_url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  const handleView = async () => {
    setPreviewError(null)
    const url = file.download_url
    if (url) {
      if (file.file_type === 'image') {
        onPreviewImage(url)
      } else {
        window.open(url, '_blank', 'noopener,noreferrer')
      }
      return
    }
    // Private file - no permanent URL, fetch a short-lived signed one on demand.
    setPreviewLoading(true)
    try {
      const signedUrl = await filesApi.getDownloadUrl(file.id)
      if (file.file_type === 'image') {
        onPreviewImage(signedUrl)
      } else {
        window.open(signedUrl, '_blank', 'noopener,noreferrer')
      }
    } catch (err) {
      setPreviewError(getErrorMessage(err))
    } finally {
      setPreviewLoading(false)
    }
  }

  return (
    <tr className="border-b border-border last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50">
      <td className="px-4 py-2.5 w-8">
        <FileTypeIcon type={file.file_type} />
      </td>
      <td className="px-4 py-2.5 min-w-0">
        <p className="text-sm text-text truncate" title={file.original_filename}>
          {file.original_filename}
        </p>
        {(previewError || downloadError) && (
          <p className="text-red-600 dark:text-red-400 text-xs mt-0.5">{previewError || downloadError}</p>
        )}
      </td>
      <td className="px-4 py-2.5 whitespace-nowrap">
        {file.category ? (
          <span className="badge badge-slate flex items-center gap-1 w-fit">
            <Folder size={10} aria-hidden="true" /> {file.category}
          </span>
        ) : (
          <span className="text-text-muted text-xs">—</span>
        )}
      </td>
      <td className="px-4 py-2.5 whitespace-nowrap text-text-secondary text-sm">{formatFileSize(file.file_size)}</td>
      <td className="px-4 py-2.5 whitespace-nowrap text-text-secondary text-sm">{formatDateTime(file.created_at)}</td>
      <td className="px-4 py-2.5 whitespace-nowrap">
        <span className={`badge ${file.is_public ? 'badge-cyan' : 'badge-slate'} flex items-center gap-1 w-fit`}>
          {file.is_public ? <Globe size={10} aria-hidden="true" /> : <Lock size={10} aria-hidden="true" />}
          {file.is_public ? 'Público' : 'Privado'}
        </span>
      </td>
      <td className="px-4 py-2.5 text-right whitespace-nowrap">
        <div className="flex justify-end items-center gap-1">
          <button
            type="button"
            onClick={handleView}
            disabled={previewLoading}
            aria-label="Ver"
            title="Ver"
            className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
          >
            <Eye size={15} />
          </button>
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            aria-label="Descargar"
            title="Descargar"
            className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
          >
            <Download size={15} />
          </button>
          {file.is_public && (
            <button
              type="button"
              onClick={handleCopyLink}
              disabled={!file.download_url}
              aria-label={copied ? 'Copiado' : 'Copiar link'}
              title={copied ? 'Copiado' : 'Copiar link'}
              className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
            >
              {copied ? <Check size={15} /> : <Copy size={15} />}
            </button>
          )}
          <button
            type="button"
            onClick={onToggleVisibility}
            disabled={isTogglingVisibility}
            aria-label={file.is_public ? 'Hacer privado' : 'Hacer público'}
            title={file.is_public ? 'Hacer privado' : 'Hacer público'}
            className="p-1.5 rounded text-text-secondary hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-cyan-600"
          >
            {file.is_public ? <Globe size={15} /> : <Lock size={15} />}
          </button>
          <button
            type="button"
            onClick={onDelete}
            aria-label="Eliminar"
            title="Eliminar"
            className="p-1.5 rounded text-text-secondary hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-600"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </td>
    </tr>
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
  const [preview, setPreview] = useState<{ filename: string; url: string } | null>(null)
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
          <div className="overflow-x-auto -mx-6">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-text-secondary">
                  <th className="px-4 py-2 font-medium"></th>
                  <th className="px-4 py-2 font-medium">Nombre</th>
                  <th className="px-4 py-2 font-medium">Carpeta</th>
                  <th className="px-4 py-2 font-medium">Tamaño</th>
                  <th className="px-4 py-2 font-medium">Subido</th>
                  <th className="px-4 py-2 font-medium">Estado</th>
                  <th className="px-4 py-2 font-medium text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {data!.map((file) => (
                  <FileRow
                    key={file.id}
                    file={file}
                    onDelete={() => handleDelete(file)}
                    onToggleVisibility={() =>
                      visibilityMutation.mutate({ id: file.id, isPublic: !file.is_public })
                    }
                    isTogglingVisibility={
                      visibilityMutation.isPending && visibilityMutation.variables?.id === file.id
                    }
                    onPreviewImage={(url) => setPreview({ filename: file.original_filename, url })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {preview && (
        <Modal title={preview.filename} onClose={() => setPreview(null)} maxWidth="max-w-4xl">
          <img src={preview.url} alt={preview.filename} className="w-full h-auto rounded-lg" />
        </Modal>
      )}
    </div>
  )
}

export default FilesPage
