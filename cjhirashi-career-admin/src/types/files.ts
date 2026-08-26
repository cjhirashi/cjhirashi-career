// Mirrors api/src/schemas/file_upload.py::FileUploadResponse
export type FileType = 'document' | 'image' | 'archive' | 'other'

export interface FileUploadEntity {
  id: string
  user_id: string
  original_filename: string
  stored_filename: string
  file_type: FileType
  mime_type: string | null
  file_size: number
  description: string | null
  category: string | null
  is_public: boolean
  download_url: string | null
  created_at: string
}
