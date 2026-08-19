import { axiosInstance } from './client'
import { FileUploadEntity } from '@/types/files'

export interface UploadFileOptions {
  description?: string
  /** Free-typed folder name - the backend slugifies it into both the row's
   * `category` and the actual S3 key prefix (real folder in the bucket). */
  category?: string
}

/**
 * Client for the MinIO-backed file bucket (`/files`). Mirrors the shape of
 * `api/src/routes/files.py` - upload/list/delete, always scoped server-side
 * to the authenticated user.
 */
export const filesApi = {
  list: async (params: { skip?: number; limit?: number; category?: string } = {}): Promise<FileUploadEntity[]> => {
    const { skip = 0, limit = 50, category } = params
    const response = await axiosInstance.get<FileUploadEntity[]>('/files', { params: { skip, limit, category } })
    return response.data
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

    const response = await axiosInstance.post<FileUploadEntity>('/files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  remove: async (id: number): Promise<void> => {
    await axiosInstance.delete(`/files/${id}`)
  },
}
