import { axiosInstance } from './client'
import { ListParams } from './career'
import { CareerEntity } from '@/types/career'

export interface PdfOutputTemplate extends CareerEntity {
  slug: string
  document_type: string
  title: string
  description?: string | null
  html_template: string
  style_id?: string | null
  variables?: string | null
  variables_schema?: Record<string, unknown> | null
  preview_notes?: string | null
  is_active: boolean
  is_default: boolean
  version: number
  created_at: string
  updated_at: string
}

export interface PdfTemplatePayload {
  slug: string
  document_type: string
  title: string
  description?: string
  html_template: string
  style_id?: string
  variables?: string
  is_default?: boolean
  is_active?: boolean
}

export const pdfTemplatesApi = {
  list: async (params: ListParams = {}): Promise<PdfOutputTemplate[]> => {
    const { skip = 0, limit = 50 } = params
    const response = await axiosInstance.get<PdfOutputTemplate[]>('/pdf-templates', {
      params: { skip, limit },
    })
    return response.data
  },

  get: async (id: string): Promise<PdfOutputTemplate> => {
    const response = await axiosInstance.get<PdfOutputTemplate>(`/pdf-templates/${id}`)
    return response.data
  },

  create: async (payload: Record<string, unknown>): Promise<PdfOutputTemplate> => {
    const response = await axiosInstance.post<PdfOutputTemplate>('/pdf-templates', payload)
    return response.data
  },

  update: async (id: string, payload: Record<string, unknown>): Promise<PdfOutputTemplate> => {
    const response = await axiosInstance.put<PdfOutputTemplate>(`/pdf-templates/${id}`, payload)
    return response.data
  },

  remove: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/pdf-templates/${id}`)
  },

  render: async (id: string, variables: Record<string, string>, title?: string): Promise<Blob> => {
    const response = await axiosInstance.post(
      `/pdf-templates/${id}/render`,
      { variables, title },
      { responseType: 'blob', timeout: 60000 }
    )
    return response.data
  },
}
