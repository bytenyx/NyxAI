import axios from 'axios'
import type { Session, SessionListItem, ChatRequest, ChatResponse, ApiResponse, PaginatedResponse } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export default api

export const sessionsApi = {
  list: (page = 1, pageSize = 20, status?: string) =>
    api.get<PaginatedResponse<SessionListItem>>('/sessions', {
      params: { page, page_size: pageSize, status }
    }).then(res => res.data.data),
  get: (id: string) =>
    api.get<ApiResponse<Session>>(`/sessions/${id}`).then(res => res.data.data),
  create: (data: { trigger_type: string; trigger_source: string; title?: string }) =>
    api.post<ApiResponse<Session>>('/sessions', data).then(res => res.data.data),
  delete: (id: string) => api.delete(`/sessions/${id}`).then(res => res.data),
}

export const chatApi = {
  message: (data: ChatRequest) =>
    api.post<ApiResponse<ChatResponse>>('/chat/message', data).then(res => res.data.data),
}
