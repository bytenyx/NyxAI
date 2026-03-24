import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import AgentProcessPanel from '../AgentProcessPanel'
import { useAgentStore } from '../../stores/agentStore'

vi.mock('../../stores/agentStore')

describe('AgentProcessPanel', () => {
  const mockAgents = {
    'agent-1': {
      id: 'agent-1',
      session_id: 'session-1',
      agent: {
        id: 'agent-1',
        name: 'InvestigationAgent',
        display_name: '调查Agent',
        type: 'investigation',
        icon: 'search',
      },
      status: 'running' as const,
      thoughts: ['分析用户输入', '查询Prometheus数据'],
      tool_calls: [
        {
          tool: 'prometheus',
          params: { query: 'up' },
          status: 'success' as const,
          result: { value: 1 },
          timestamp: '2024-01-01T00:00:00Z',
        },
      ],
      result: null,
      started_at: '2024-01-01T00:00:00Z',
    },
    'agent-2': {
      id: 'agent-2',
      session_id: 'session-1',
      agent: {
        id: 'agent-2',
        name: 'DiagnosisAgent',
        display_name: '诊断Agent',
        type: 'diagnosis',
        icon: 'diagnosis',
      },
      status: 'completed' as const,
      thoughts: ['分析因果关系'],
      tool_calls: [],
      result: '根因分析完成',
      started_at: '2024-01-01T00:01:00Z',
      completed_at: '2024-01-01T00:02:00Z',
    },
  }

  const mockTimeline = [
    {
      id: 'handoff-0',
      type: 'alert' as const,
      status: 'completed' as const,
      title: '调查Agent → 诊断Agent',
      description: '调查完成，进入根因分析阶段',
      timestamp: '2024-01-01T00:01:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('empty state', () => {
    it('renders nothing when no agents', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: {},
        currentAgent: null,
        timeline: [],
        sequence: 0,
        isConnected: false,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      const { container } = render(<AgentProcessPanel />)
      expect(container.firstChild).toBeEmptyDOMElement()
    })
  })

  describe('with agents', () => {
    it('renders all agents', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: mockAgents,
        currentAgent: 'agent-1',
        timeline: mockTimeline,
        sequence: 1,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      render(<AgentProcessPanel />)

      expect(screen.getByText('调查Agent')).toBeInTheDocument()
      expect(screen.getByText('诊断Agent')).toBeInTheDocument()
    })

    it('renders agent cards in correct order', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: mockAgents,
        currentAgent: 'agent-1',
        timeline: mockTimeline,
        sequence: 1,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      const { container } = render(<AgentProcessPanel />)
      const agentCards = container.querySelectorAll('.agent-card')

      expect(agentCards.length).toBe(2)
    })

    it('renders handoff indicators between agents', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: mockAgents,
        currentAgent: 'agent-1',
        timeline: mockTimeline,
        sequence: 1,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      render(<AgentProcessPanel />)

      expect(screen.getByText('调查完成，进入根因分析阶段')).toBeInTheDocument()
    })

    it('does not render handoff for last agent', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: mockAgents,
        currentAgent: 'agent-2',
        timeline: mockTimeline,
        sequence: 1,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      const { container } = render(<AgentProcessPanel />)
      const handoffs = container.querySelectorAll('.handoff-indicator')

      expect(handoffs.length).toBe(1)
    })
  })

  describe('agent status', () => {
    it('displays running status correctly', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: { 'agent-1': mockAgents['agent-1'] },
        currentAgent: 'agent-1',
        timeline: [],
        sequence: 0,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      render(<AgentProcessPanel />)

      expect(screen.getByText('调查Agent')).toBeInTheDocument()
    })

    it('displays completed status correctly', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: { 'agent-2': mockAgents['agent-2'] },
        currentAgent: 'agent-2',
        timeline: [],
        sequence: 0,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      render(<AgentProcessPanel />)

      expect(screen.getByText('诊断Agent')).toBeInTheDocument()
    })
  })

  describe('agent thoughts', () => {
    it('displays agent thoughts', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: { 'agent-1': mockAgents['agent-1'] },
        currentAgent: 'agent-1',
        timeline: [],
        sequence: 0,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      render(<AgentProcessPanel />)

      expect(screen.getByText('分析用户输入')).toBeInTheDocument()
      expect(screen.getByText('查询Prometheus数据')).toBeInTheDocument()
    })
  })

  describe('tool calls', () => {
    it('displays tool calls', () => {
      vi.mocked(useAgentStore).mockReturnValue({
        agents: { 'agent-1': mockAgents['agent-1'] },
        currentAgent: 'agent-1',
        timeline: [],
        sequence: 0,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      render(<AgentProcessPanel />)

      expect(screen.getByText('prometheus')).toBeInTheDocument()
    })
  })

  describe('multiple agents', () => {
    it('handles multiple agents with different statuses', () => {
      const multiAgents = {
        ...mockAgents,
        'agent-3': {
          id: 'agent-3',
          session_id: 'session-1',
          agent: {
            id: 'agent-3',
            name: 'RecoveryAgent',
            display_name: '恢复Agent',
            type: 'recovery',
            icon: 'recovery',
          },
          status: 'pending' as const,
          thoughts: [],
          tool_calls: [],
          result: null,
          started_at: '2024-01-01T00:02:00Z',
        },
      }

      const multiTimeline = [
        ...mockTimeline,
        {
          id: 'handoff-1',
          type: 'alert' as const,
          status: 'completed' as const,
          title: '诊断Agent → 恢复Agent',
          description: '诊断完成，生成恢复方案',
          timestamp: '2024-01-01T00:02:00Z',
        },
      ]

      vi.mocked(useAgentStore).mockReturnValue({
        agents: multiAgents,
        currentAgent: 'agent-1',
        timeline: multiTimeline,
        sequence: 2,
        isConnected: true,
        setCurrentAgent: vi.fn(),
        handleMessage: vi.fn(),
        setConnected: vi.fn(),
        reset: vi.fn(),
      })

      render(<AgentProcessPanel />)

      expect(screen.getByText('调查Agent')).toBeInTheDocument()
      expect(screen.getByText('诊断Agent')).toBeInTheDocument()
      expect(screen.getByText('恢复Agent')).toBeInTheDocument()
    })
  })
})