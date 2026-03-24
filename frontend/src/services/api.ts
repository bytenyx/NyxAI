import axios from 'axios'
import type { Session, SessionListItem, ChatRequest, ChatResponse, ApiResponse, PaginatedResponse } from '../types'
import type { AgentExecution } from '../types/agent'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export default api

export const sessionsApi = {
  list: (page = 1, pageSize = 20, status?: string) =>
    api.get<PaginatedResponse<SessionListItem>>('/sessions', {
      params: { page, page_size: pageSize, status }
    }).then(res => res.data),
  get: (id: string) =>
    api.get<ApiResponse<Session>>(`/sessions/${id}`).then(res => res.data.data),
  getExecutions: (id: string) =>
    api.get<ApiResponse<AgentExecution[]>>(`/sessions/${id}/executions`).then(res => res.data.data),
  create: (data: { trigger_type: string; trigger_source: string; title?: string }) =>
    api.post<ApiResponse<Session>>('/sessions', data).then(res => res.data.data),
  delete: (id: string) =>
    api.delete<ApiResponse<null>>(`/sessions/${id}`).then(res => res.data),
}

export const chatApi = {
  message: (data: ChatRequest) =>
    api.post<ApiResponse<ChatResponse>>('/chat/message', data).then(res => res.data.data),
}
