export interface Session {
  id: string
  trigger_type: string
  trigger_source: string
  status: 'investigating' | 'diagnosing' | 'recovering' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

export interface SessionListItem {
  id: string
  title: string
  trigger_type: string
  trigger_source: string
  status: 'investigating' | 'diagnosing' | 'recovering' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  message_count?: number
  last_message?: string
}

export interface ChatRequest {
  session_id?: string
  message: string
}

export interface ChatResponse {
  session_id: string
  response: string
  status: string
}

export interface Evidence {
  id: string
  evidence_type: 'metric' | 'log' | 'trace' | 'knowledge'
  description: string
  source_data: Record<string, unknown>
  source_system: string
  timestamp: string
  confidence: number
}

export interface EvidenceNode {
  id: string
  description: string
  evidence: Evidence
  supports: string[]
  contradicts: string[]
  inference_step: string
}
