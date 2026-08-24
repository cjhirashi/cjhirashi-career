import { axiosInstance } from './client'
import { ListParams } from './career'
import { CareerEntity } from '@/types/career'

export interface PdfTemplateStyle extends CareerEntity {
  slug: string
  title: string
  description?: string | null
  css_content: string
  style_guide?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export const pdfTemplateStylesApi = {
  list: async (params: ListParams = {}): Promise<PdfTemplateStyle[]> => {
    const { skip = 0, limit = 50 } = params
    const response = await axiosInstance.get<PdfTemplateStyle[]>('/pdf-template-styles', {
      params: { skip, limit },
    })
    return response.data
  },

  get: async (id: string): Promise<PdfTemplateStyle> => {
    const response = await axiosInstance.get<PdfTemplateStyle>(`/pdf-template-styles/${id}`)
    return response.data
  },

  create: async (payload: Record<string, unknown>): Promise<PdfTemplateStyle> => {
    const response = await axiosInstance.post<PdfTemplateStyle>('/pdf-template-styles', payload)
    return response.data
  },

  update: async (id: string, payload: Record<string, unknown>): Promise<PdfTemplateStyle> => {
    const response = await axiosInstance.put<PdfTemplateStyle>(`/pdf-template-styles/${id}`, payload)
    return response.data
  },

  remove: async (id: string): Promise<void> => {
    await axiosInstance.delete(`/pdf-template-styles/${id}`)
  },
}
