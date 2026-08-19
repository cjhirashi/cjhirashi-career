import React, { useRef, useState } from 'react'
import { Copy, Check, FileArchive, FileText, File as FileIcon, Trash2, Upload } from 'lucide-react'
import { useFilesList, useFileMutations } from '@/hooks/useFiles'
import { FileUploadEntity } from '@/types/files'
import { getErrorMessage } from '@/utils/errors'
import { formatFileSize, formatDateTime } from '@/utils/formatters'
import { LoadingSpinner } from '@/components/LoadingSpinner'

const FileTypeIcon: React.FC<{ type: FileUploadEntity['file_type'] }> = ({ type }) => {
  if (type === 'document') return <FileText size={28} className="text-text-secondary" aria-hidden="true" />
  if (type === 'archive') return <FileArchive size={28} className="text-text-secondary" aria-hidden="true" />
  return <FileIcon size={28} className="text-text-secondary" aria-hidden="true" />
}

const FileCard: React.FC<{ file: FileUploadEntity; onDelete: () => void }> = ({ file, onDelete }) => {
  const [copied, setCopied] = useState(false)

  const handleCopyLink = () => {
    if (!file.download_url) return
    navigator.clipboard.writeText(file.download_url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="aspect-video rounded-lg overflow-hidden flex items-center justify-center bg-glass">
        {file.file_type === 'image' && file.download_url ? (
          <img src={file.download_url} alt={file.original_filename} className="w-full h-full object-cover" />
        ) : (
          <FileTypeIcon type={file.file_type} />
        )}
      </div>

      <div className="min-w-0">
        <p className="text-sm font-medium text-text truncate" title={file.original_filename}>
          {file.original_filename}
        </p>
        <p className="text-xs text-text-secondary">
          {formatFileSize(file.file_size)} · {formatDateTime(file.created_at)}
        </p>
      </div>

      <div className="flex items-center gap-2 mt-auto">
        <button
          type="button"
          onClick={handleCopyLink}
          className="btn-secondary btn-small flex-1 flex items-center justify-center gap-1"
          disabled={!file.download_url}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Copiado' : 'Copiar link'}
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
  const { data, isLoading, isError, error, refetch } = useFilesList()
  const { uploadMutation, deleteMutation } = useFileMutations()
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setUploadError(null)
    uploadMutation.mutate(
      { file },
      { onError: (err) => setUploadError(getErrorMessage(err)) }
    )
  }

  const handleDelete = (file: FileUploadEntity) => {
    if (!window.confirm(`¿Eliminar "${file.original_filename}"? Esta acción no se puede deshacer.`)) return
    deleteMutation.mutate(file.id)
  }

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between gap-3">
        <h2 className="font-semibold text-text">Archivos</h2>
        <div>
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
            No has subido ningún archivo todavía.
          </p>
        )}

        {!isLoading && !isError && (data?.length ?? 0) > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data!.map((file) => (
              <FileCard key={file.id} file={file} onDelete={() => handleDelete(file)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default FilesPage
