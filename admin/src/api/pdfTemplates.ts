import { axiosInstance } from './client'

export interface PdfOutputTemplate {
  id: string
  user_id: string
  slug: string
  document_type: string
  title: string
  description?: string | null
  html_template: string
  css_content?: string | null
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
  css_content?: string
  is_default?: boolean
  is_active?: boolean
}

export const pdfTemplatesApi = {
  list: async (documentType?: string): Promise<PdfOutputTemplate[]> => {
    const response = await axiosInstance.get<PdfOutputTemplate[]>('/pdf-templates', {
      params: documentType ? { document_type: documentType } : undefined,
    })
    return response.data
  },

  get: async (id: string): Promise<PdfOutputTemplate> => {
    const response = await axiosInstance.get<PdfOutputTemplate>(`/pdf-templates/${id}`)
    return response.data
  },

  create: async (payload: PdfTemplatePayload): Promise<PdfOutputTemplate> => {
    const response = await axiosInstance.post<PdfOutputTemplate>('/pdf-templates', payload)
    return response.data
  },

  update: async (id: string, payload: Partial<PdfTemplatePayload>): Promise<PdfOutputTemplate> => {
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
      { responseType: 'blob' }
    )
    return response.data
  },
}
