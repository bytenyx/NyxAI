import api from './api'
import type { Knowledge, KnowledgeCreate, KnowledgeUpdate } from '../types/knowledge'

const BASE_URL = '/knowledge'

export const knowledgeApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    type?: string
    tags?: string
    search?: string
  }): Promise<Knowledge[]> => {
    const response = await api.get(BASE_URL, { params })
    return response.data
  },

  get: async (id: string): Promise<Knowledge> => {
    const response = await api.get(`${BASE_URL}/${id}`)
    return response.data
  },

  create: async (data: KnowledgeCreate): Promise<Knowledge> => {
    const response = await api.post(BASE_URL, data)
    return response.data
  },

  update: async (id: string, data: KnowledgeUpdate): Promise<Knowledge> => {
    const response = await api.put(`${BASE_URL}/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${id}`)
  },

  upload: async (
    file: File,
    metadata?: {
      title?: string
      tags?: string
      category?: string
    }
  ): Promise<Knowledge> => {
    const formData = new FormData()
    formData.append('file', file)
    if (metadata?.title) formData.append('title', metadata.title)
    if (metadata?.tags) formData.append('tags', metadata.tags)
    if (metadata?.category) formData.append('category', metadata.category)

    const response = await api.post(`${BASE_URL}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  getTags: async (): Promise<string[]> => {
    const response = await api.get(`${BASE_URL}/tags`)
    return response.data
  },
}
