import { axiosInstance } from './client'
import { FileType, FileUploadEntity } from '@/types/files'

export interface UploadFileOptions {
  description?: string
  /** Free-typed folder name - the backend slugifies it into both the row's
   * `category` and the actual S3 key prefix (real folder in the bucket). */
  category?: string
  /** Defaults to true server-side. Public files get a permanent download_url;
   * private ones have none - see filesApi.getDownloadUrl. */
  isPublic?: boolean
}

/**
 * Client for the MinIO-backed file bucket (`/files`). Mirrors the shape of
 * `api/src/routes/files.py` - upload/list/delete, always scoped server-side
 * to the authenticated user.
 */
export const filesApi = {
  list: async (
    params: { skip?: number; limit?: number; category?: string; fileType?: FileType } = {}
  ): Promise<FileUploadEntity[]> => {
    const { skip = 0, limit = 50, category, fileType } = params
    const response = await axiosInstance.get<FileUploadEntity[]>('/files', {
      params: { skip, limit, category, file_type: fileType },
    })
    return response.data
  },

  count: async (): Promise<number> => {
    const response = await axiosInstance.get<{ count: number }>('/files/count')
    return response.data.count
  },

  categories: async (): Promise<string[]> => {
    const response = await axiosInstance.get<string[]>('/files/categories')
    return response.data
  },

  upload: async (file: File, options: UploadFileOptions = {}): Promise<FileUploadEntity> => {
    const formData = new FormData()
    formData.append('file', file)
    if (options.description) formData.append('description', options.description)
    if (options.category) formData.append('category', options.category)
    if (options.isPublic !== undefined) formData.append('is_public', String(options.isPublic))

    const response = await axiosInstance.post<FileUploadEntity>('/files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  setVisibility: async (id: string, isPublic: boolean): Promise<FileUploadEntity> => {
    const response = await axiosInstance.patch<FileUploadEntity>(`/files/${id}/visibility`, {
      is_public: isPublic,
    })
    return response.data
  },

  /** Short-lived signed URL - the only way to read a private file, and also
   * usable for a public one (e.g. to preview without trusting the stored
   * download_url yet). */
  getDownloadUrl: async (id: string): Promise<string> => {
    const response = await axiosInstance.get<{ url: string }>(`/files/${id}/download`)
    return response.data.url
  },

  /** Raw file bytes, authenticated the normal way (JWT header via
   * axiosInstance) - used to force a real "Save As" download via a Blob.
   * A plain link to the bucket URL just navigates/opens it instead. */
  downloadBlob: async (id: string): Promise<Blob> => {
    const response = await axiosInstance.get(`/files/${id}/raw`, { responseType: 'blob' })
    return response.data
  },

  remove: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/files/${id}`)
  },
}
