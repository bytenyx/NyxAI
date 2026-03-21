import axios from 'axios'
import type { Session, SessionListItem, ChatRequest, ChatResponse } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export default api

export const sessionsApi = {
  list: () => api.get<SessionListItem[]>('/sessions'),
  get: (id: string) => api.get<Session>(`/sessions/${id}`),
  create: (data: { trigger_type: string; trigger_source: string }) =>
    api.post<Session>('/sessions', data),
  delete: (id: string) => api.delete(`/sessions/${id}`),
}

export const chatApi = {
  message: (data: ChatRequest) => api.post<ChatResponse>('/chat/message', data),
}
