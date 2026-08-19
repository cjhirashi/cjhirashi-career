import { axiosInstance } from './client'
import { FileUploadEntity } from '@/types/files'

/**
 * Client for the MinIO-backed file bucket (`/files`). Mirrors the shape of
 * `api/src/routes/files.py` - upload/list/delete, always scoped server-side
 * to the authenticated user.
 */
export const filesApi = {
  list: async (params: { skip?: number; limit?: number } = {}): Promise<FileUploadEntity[]> => {
    const { skip = 0, limit = 50 } = params
    const response = await axiosInstance.get<FileUploadEntity[]>('/files', { params: { skip, limit } })
    return response.data
  },

  upload: async (file: File, description?: string): Promise<FileUploadEntity> => {
    const formData = new FormData()
    formData.append('file', file)
    if (description) formData.append('description', description)

    const response = await axiosInstance.post<FileUploadEntity>('/files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  remove: async (id: number): Promise<void> => {
    await axiosInstance.delete(`/files/${id}`)
  },
}
