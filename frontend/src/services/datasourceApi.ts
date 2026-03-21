import api from './api'
import type { DataSource, DataSourceCreate, DataSourceUpdate, DataSourceTestResult } from '../types/datasource'

const BASE_URL = '/datasources'

export const datasourceApi = {
  list: async (): Promise<DataSource[]> => {
    const response = await api.get(BASE_URL)
    return response.data
  },

  get: async (id: string): Promise<DataSource> => {
    const response = await api.get(`${BASE_URL}/${id}`)
    return response.data
  },

  create: async (data: DataSourceCreate): Promise<DataSource> => {
    const response = await api.post(BASE_URL, data)
    return response.data
  },

  update: async (id: string, data: DataSourceUpdate): Promise<DataSource> => {
    const response = await api.put(`${BASE_URL}/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${id}`)
  },

  test: async (id: string): Promise<DataSourceTestResult> => {
    const response = await api.post(`${BASE_URL}/${id}/test`)
    return response.data
  },
}
