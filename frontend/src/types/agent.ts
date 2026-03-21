export interface AgentIdentity {
  id: string
  name: string
  display_name: string
  type: 'investigation' | 'diagnosis' | 'recovery' | 'orchestrator'
  icon?: string
}

export interface ToolCallRecord {
  tool: string
  params: Record<string, unknown>
  result?: unknown
  status: 'pending' | 'running' | 'success' | 'error'
  timestamp: string
}

export interface AgentExecution {
  id: string
  session_id: string
  agent: AgentIdentity
  status: 'idle' | 'running' | 'completed' | 'failed'
  thoughts: string[]
  tool_calls: ToolCallRecord[]
  result?: string
  started_at: string
  completed_at?: string
  duration_ms?: number
}

export interface ServerMessage {
  type: string
  agent?: AgentIdentity
  payload: unknown
  timestamp: string
  sequence: number
}

export interface TimelineNode {
  id: string
  type: 'alert' | 'investigation' | 'diagnosis' | 'recovery' | 'complete'
  status: 'pending' | 'running' | 'completed' | 'failed'
  title: string
  description?: string
  timestamp: string
  duration?: number
  agent?: AgentIdentity
}
