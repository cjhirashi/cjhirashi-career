import { axiosInstance } from './client'
import { AdminSection, AdminSectionUpdate } from '@/types/adminSections'

const CONTROL_PLANE_TIMEOUT_MS = 20000

export const adminSectionsApi = {
  list: async (): Promise<AdminSection[]> => {
    const response = await axiosInstance.get<AdminSection[]>('/admin/sections', {
      timeout: CONTROL_PLANE_TIMEOUT_MS,
    })
    return response.data
  },

  get: async (sectionId: string): Promise<AdminSection> => {
    const response = await axiosInstance.get<AdminSection>(`/admin/sections/${sectionId}`, {
      timeout: CONTROL_PLANE_TIMEOUT_MS,
    })
    return response.data
  },

  update: async (sectionId: string, payload: AdminSectionUpdate): Promise<AdminSection> => {
    const response = await axiosInstance.put<AdminSection>(`/admin/sections/${sectionId}`, payload, {
      timeout: CONTROL_PLANE_TIMEOUT_MS,
    })
    return response.data
  },
}
