import axios from 'axios'
import type { Session, ChatRequest, ChatResponse } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export const sessionsApi = {
  list: () => api.get<Session[]>('/sessions'),
  get: (id: string) => api.get<Session>(`/sessions/${id}`),
  create: (data: { trigger_type: string; trigger_source: string }) =>
    api.post<Session>('/sessions', data),
}

export const chatApi = {
  message: (data: ChatRequest) => api.post<ChatResponse>('/chat/message', data),
}
