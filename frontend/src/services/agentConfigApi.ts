import api from './api'
import type { AgentConfig, AgentConfigCreate, AgentConfigUpdate, AgentConfigVersion, SkillMetadata } from '../types/agentConfig'

export const agentConfigApi = {
  list: () =>
    api.get<{ data: AgentConfig[] }>('/agent-configs').then(res => res.data.data),

  getByType: (agentType: string) =>
    api.get<{ data: AgentConfig }>(`/agent-configs/${agentType}`).then(res => res.data.data),

  create: (data: AgentConfigCreate) =>
    api.post<{ data: AgentConfig }>('/agent-configs', data).then(res => res.data.data),

  update: (id: string, data: AgentConfigUpdate) =>
    api.put<{ data: AgentConfig }>(`/agent-configs/${id}`, data).then(res => res.data.data),

  delete: (id: string) =>
    api.delete(`/agent-configs/${id}`).then(res => res.data),

  activate: (id: string) =>
    api.post<{ data: AgentConfig }>(`/agent-configs/${id}/activate`).then(res => res.data.data),

  getVersions: (id: string) =>
    api.get<{ data: AgentConfigVersion[] }>(`/agent-configs/${id}/versions`).then(res => res.data.data),

  rollback: (id: string, version: number) =>
    api.post<{ data: AgentConfig }>(`/agent-configs/${id}/rollback/${version}`).then(res => res.data.data),

  listSkills: () =>
    api.get<{ skills: SkillMetadata[] }>('/agent-configs/skills/list').then(res => res.data.skills),
}
