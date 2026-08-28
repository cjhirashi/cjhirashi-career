import { axiosInstance } from './client'
import {
  AdminViewItem,
  AdminViewUpdateRequest,
  NavTreeResponse,
  SectionDetail,
  SectionGroupItem,
  SectionListItem,
  SectionReorderRequest,
  SectionReparentRequest,
} from '@/types/adminSections'

const CONTROL_PLANE_TIMEOUT_MS = 20000
const opts = { timeout: CONTROL_PLANE_TIMEOUT_MS }

export const adminNavTreeApi = {
  get: async (): Promise<NavTreeResponse> => {
    const response = await axiosInstance.get<NavTreeResponse>('/admin/nav-tree', opts)
    return response.data
  },
}

export const adminSectionGroupsApi = {
  list: async (): Promise<SectionGroupItem[]> => {
    const response = await axiosInstance.get<SectionGroupItem[]>('/admin/section-groups', opts)
    return response.data
  },

  reorder: async (order: string[]): Promise<SectionGroupItem[]> => {
    const response = await axiosInstance.put<SectionGroupItem[]>(
      '/admin/section-groups/order',
      { order },
      opts
    )
    return response.data
  },

  update: async (grpId: string, sortOrder: number): Promise<SectionGroupItem> => {
    const response = await axiosInstance.put<SectionGroupItem>(
      `/admin/section-groups/${grpId}`,
      { sort_order: sortOrder },
      opts
    )
    return response.data
  },
}

export const adminSectionsApi = {
  /** `level` = 'l1' | 'l2' | 'l3'. */
  listByLevel: async (level: 'l1' | 'l2' | 'l3'): Promise<SectionListItem[]> => {
    const response = await axiosInstance.get<SectionListItem[]>(`/admin/sections/${level}`, opts)
    return response.data
  },

  get: async (sectionId: string): Promise<SectionDetail> => {
    const response = await axiosInstance.get<SectionDetail>(`/admin/sections/${sectionId}`, opts)
    return response.data
  },

  update: async (sectionId: string, payload: SectionReparentRequest): Promise<SectionDetail> => {
    const response = await axiosInstance.put<SectionDetail>(
      `/admin/sections/${sectionId}`,
      payload,
      opts
    )
    return response.data
  },

  reorder: async (payload: SectionReorderRequest): Promise<SectionListItem[]> => {
    const response = await axiosInstance.put<SectionListItem[]>(
      '/admin/sections/order',
      payload,
      opts
    )
    return response.data
  },
}

export const adminViewsApi = {
  list: async (filters?: {
    section_id?: string
    responsible?: string
    data_source?: string
  }): Promise<AdminViewItem[]> => {
    const response = await axiosInstance.get<AdminViewItem[]>('/admin/views', {
      ...opts,
      params: filters,
    })
    return response.data
  },

  get: async (viewId: string): Promise<AdminViewItem> => {
    const response = await axiosInstance.get<AdminViewItem>(`/admin/views/${viewId}`, opts)
    return response.data
  },

  update: async (viewId: string, payload: AdminViewUpdateRequest): Promise<AdminViewItem> => {
    const response = await axiosInstance.put<AdminViewItem>(
      `/admin/views/${viewId}`,
      payload,
      opts
    )
    return response.data
  },
}
