export interface AgentConfig {
  id: string
  agent_type: string
  name: string
  system_prompt: string
  allowed_skills: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AgentConfigCreate {
  agent_type: string
  name: string
  system_prompt: string
  allowed_skills?: string[]
}

export interface AgentConfigUpdate {
  name?: string
  system_prompt?: string
  allowed_skills?: string[]
  change_reason?: string
}

export interface AgentConfigVersion {
  id: string
  config_id: string
  version: number
  system_prompt: string
  allowed_skills: string[]
  changed_by: string | null
  change_reason: string | null
  created_at: string
}

export interface SkillMetadata {
  name: string
  description: string
  path: string
}
