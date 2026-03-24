import axios from 'axios'
import type { Session, SessionListItem, ChatRequest, ChatResponse } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export default api

export const sessionsApi = {
  list: () => api.get<SessionListItem[]>('/sessions').then(res => res.data),
  get: (id: string) => api.get<Session>(`/sessions/${id}`).then(res => res.data),
  create: (data: { trigger_type: string; trigger_source: string; title?: string }) =>
    api.post<Session>('/sessions', data).then(res => res.data),
  delete: (id: string) => api.delete(`/sessions/${id}`).then(res => res.data),
}

export const chatApi = {
  message: (data: ChatRequest) => api.post<ChatResponse>('/chat/message', data).then(res => res.data),
}
