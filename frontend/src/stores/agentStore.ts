import { create } from 'zustand'
import type { AgentIdentity, AgentExecution, TimelineNode, ServerMessage } from '../types/agent'

interface SessionStateCache {
  agents: Record<string, AgentExecution>
  timeline: TimelineNode[]
  sequence: number
  hasRunningAgent: boolean
}

interface AgentState {
  agents: Record<string, AgentExecution>
  currentAgent: string | null
  currentSessionId: string | null
  timeline: TimelineNode[]
  sequence: number
  isConnected: boolean
  sessionStates: Record<string, SessionStateCache>

  setCurrentAgent: (agentId: string | null) => void
  setCurrentSessionId: (sessionId: string | null) => void
  handleMessage: (message: ServerMessage) => void
  setConnected: (connected: boolean) => void
  reset: () => void
  saveSessionState: (sessionId: string) => void
  restoreSessionState: (sessionId: string) => boolean
  loadFromHistory: (executions: AgentExecution[]) => void
  hasRunningAgent: () => boolean
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: {},
  currentAgent: null,
  currentSessionId: null,
  timeline: [],
  sequence: 0,
  isConnected: false,
  sessionStates: {},

  setCurrentAgent: (agentId) => set({ currentAgent: agentId }),

  setCurrentSessionId: (sessionId) => set({ currentSessionId: sessionId }),

  hasRunningAgent: () => {
    const { agents } = get()
    return Object.values(agents).some((agent) => agent.status === 'running')
  },

  saveSessionState: (sessionId) => {
    const { agents, timeline, sequence } = get()
    const hasRunning = Object.values(agents).some((agent) => agent.status === 'running')
    
    set((state) => ({
      sessionStates: {
        ...state.sessionStates,
        [sessionId]: {
          agents: { ...agents },
          timeline: [...timeline],
          sequence,
          hasRunningAgent: hasRunning,
        },
      },
    }))
  },

  restoreSessionState: (sessionId) => {
    const { sessionStates } = get()
    const cached = sessionStates[sessionId]
    
    if (cached) {
      set({
        agents: cached.agents,
        timeline: cached.timeline,
        sequence: cached.sequence,
        currentSessionId: sessionId,
      })
      return true
    }
    return false
  },

  handleMessage: (message) => {
    const { agents, timeline, sequence, currentSessionId } = get()
    
    if (message.session_id && message.session_id !== currentSessionId) {
      return
    }
    
    const newAgents = { ...agents }
    let newTimeline = [...timeline]

    switch (message.type) {
      case 'orchestrator_status':
        newAgents = {}
        newTimeline = [
          {
            id: `orchestrator-${sequence}`,
            type: 'alert',
            status: 'running',
            title: '编排器启动',
            timestamp: message.timestamp,
          },
        ]
        break

      case 'agent_start':
        if (message.agent) {
          const exec: AgentExecution = {
            id: message.agent.id,
            session_id: '',
            agent: message.agent,
            status: 'running',
            thoughts: [],
            tool_calls: [],
            started_at: message.timestamp,
          }
          newAgents[message.agent.id] = exec

          newTimeline.push({
            id: `${message.agent.id}-${sequence}`,
            type: message.agent.type as TimelineNode['type'],
            status: 'running',
            title: message.agent.display_name,
            description: (message.payload as { description?: string })?.description,
            timestamp: message.timestamp,
            agent: message.agent,
          })
        }
        break

      case 'agent_thinking':
        if (message.agent && newAgents[message.agent.id]) {
          const thought = (message.payload as { thought: string }).thought
          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            thoughts: [...newAgents[message.agent.id].thoughts, thought],
          }
        }
        break

      case 'tool_call':
        if (message.agent && newAgents[message.agent.id]) {
          const toolCall = {
            ...(message.payload as object),
            status: 'running',
            timestamp: message.timestamp,
          } as AgentExecution['tool_calls'][0]
          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            tool_calls: [...newAgents[message.agent.id].tool_calls, toolCall],
          }
        }
        break

      case 'tool_result':
        if (message.agent && newAgents[message.agent.id]) {
          const toolCalls = [...newAgents[message.agent.id].tool_calls]
          const lastCall = toolCalls[toolCalls.length - 1]
          if (lastCall) {
            lastCall.result = (message.payload as { result: unknown }).result
            lastCall.status = 'success'
          }
          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            tool_calls: toolCalls,
          }
        }
        break

      case 'agent_complete':
        if (message.agent && newAgents[message.agent.id]) {
          const startedAt = newAgents[message.agent.id].started_at
          const completedAt = message.timestamp
          const durationMs = startedAt 
            ? new Date(completedAt).getTime() - new Date(startedAt).getTime() 
            : undefined

          newAgents[message.agent.id] = {
            ...newAgents[message.agent.id],
            status: 'completed',
            result: (message.payload as { summary?: string }).summary,
            completed_at: completedAt,
            duration_ms: durationMs,
          }

          const timelineIdx = newTimeline.findIndex((n) => n.id.startsWith(`${message.agent!.id}-`))
          if (timelineIdx >= 0) {
            newTimeline[timelineIdx] = {
              ...newTimeline[timelineIdx],
              status: 'completed',
              description: (message.payload as { summary?: string }).summary,
            }
          }
        }
        break

      case 'handoff': {
        const payload = message.payload as { to_agent: AgentIdentity; context: string }
        newTimeline.push({
          id: `handoff-${sequence}`,
          type: 'alert',
          status: 'completed',
          title: `${message.agent?.display_name} → ${payload.to_agent.display_name}`,
          description: payload.context,
          timestamp: message.timestamp,
        })
        break
      }

      case 'session_complete':
        newTimeline.push({
          id: `complete-${sequence}`,
          type: 'complete',
          status: 'completed',
          title: '会话完成',
          timestamp: message.timestamp,
        })
        break
    }

    set({ agents: newAgents, timeline: newTimeline, sequence: sequence + 1 })
  },

  setConnected: (connected) => set({ isConnected: connected }),

  reset: () =>
    set({
      agents: {},
      currentAgent: null,
      timeline: [],
      sequence: 0,
    }),

  loadFromHistory: (executions) => {
    const newAgents: Record<string, AgentExecution> = {}
    const newTimeline: TimelineNode[] = []
    let sequence = 0

    executions.forEach((exec) => {
      newAgents[exec.id] = exec

      newTimeline.push({
        id: `${exec.id}-${sequence}`,
        type: exec.agent.type as TimelineNode['type'],
        status: exec.status as TimelineNode['status'],
        title: exec.agent.display_name,
        description: exec.result,
        timestamp: exec.started_at,
        agent: exec.agent,
      })

      sequence++
    })

    set({
      agents: newAgents,
      timeline: newTimeline,
      sequence,
    })
  },
}))
